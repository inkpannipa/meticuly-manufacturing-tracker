import {useEffect, useMemo, useState} from 'react'
import {Activity, ArrowRight, Box, Check, ChevronRight, ClipboardList, Factory, Gauge, LayoutDashboard, Menu, Plus, Search, Timer, TriangleAlert, X} from 'lucide-react'
import {api} from './api'

const emptyForm = {product: '', customer: '', quantity: 1, priority: 'normal'}
const priorityLabel = {normal: 'Normal', high: 'High', urgent: 'Urgent'}

function App() {
  const [dashboard, setDashboard] = useState(null)
  const [orders, setOrders] = useState([])
  const [steps, setSteps] = useState([])
  const [resources, setResources] = useState([])
  const [query, setQuery] = useState('')
  const [stepFilter, setStepFilter] = useState('all')
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [usage, setUsage] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [mobileNav, setMobileNav] = useState(false)

  const load = async () => {
    try {
      const [d, o, s, r] = await api.bootstrap()
      setDashboard(d); setOrders(o); setSteps(s); setResources(r); setError('')
    } catch (e) { setError(e.message) }
  }
  useEffect(() => { load() }, [])

  const visibleOrders = useMemo(() => orders.filter(order => {
    const matchesText = `${order.code} ${order.product} ${order.customer}`.toLowerCase().includes(query.toLowerCase())
    const matchesStep = stepFilter === 'all' || (stepFilter === 'completed' ? order.status === 'completed' : order.current_step?.id === Number(stepFilter))
    return matchesText && matchesStep
  }), [orders, query, stepFilter])

  const createOrder = async (event) => {
    event.preventDefault(); setBusy(true)
    try { await api.createOrder({...form, quantity: Number(form.quantity)}); setModal(null); setForm(emptyForm); await load() }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  const advanceOrder = async () => {
    setBusy(true)
    const consumptions = Object.entries(usage).filter(([, amount]) => Number(amount) > 0)
      .map(([resource_id, amount]) => ({resource_id: Number(resource_id), amount: Number(amount)}))
    try { await api.advance(modal.id, {consumptions}); setModal(null); setUsage({}); await load() }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  return <div className="app-shell">
    <aside className={mobileNav ? 'sidebar open' : 'sidebar'}>
      <div className="brand"><div className="brand-mark"><Factory size={19}/></div><span>METICULY</span><button className="mobile-close" onClick={() => setMobileNav(false)}><X/></button></div>
      <nav>
        <a className="active" href="#dashboard"><LayoutDashboard/>Overview</a>
        <a href="#orders"><ClipboardList/>Orders<span className="nav-count">{dashboard?.active_orders || 0}</span></a>
        <a href="#resources"><Gauge/>Resources</a>
      </nav>
      <div className="sidebar-bottom"><div className="plant"><span className="status-dot"/><div><strong>Production online</strong><small>All systems operational</small></div></div><p>Meticuly Flow <span>v1.0</span></p></div>
    </aside>

    <main>
      <header><button className="menu-btn" onClick={() => setMobileNav(true)}><Menu/></button><div><p className="eyebrow">MANUFACTURING CONTROL</p><h1>Production overview</h1></div><button className="primary" onClick={() => setModal('create')}><Plus size={18}/> New order</button></header>

      {error && <div className="error"><TriangleAlert size={18}/>{error}<button onClick={() => setError('')}><X size={16}/></button></div>}

      <section id="dashboard" className="metrics">
        <Metric icon={<Box/>} label="Total orders" value={dashboard?.total_orders ?? '—'} note="All production orders" />
        <Metric icon={<Activity/>} label="In production" value={dashboard?.active_orders ?? '—'} note="Across active stages" accent />
        <Metric icon={<Check/>} label="Completed" value={dashboard?.completed_orders ?? '—'} note="Ready for dispatch" />
        <Metric icon={<Timer/>} label="Urgent" value={dashboard?.urgent_orders ?? '—'} note="Needs attention" warning />
      </section>

      <section className="panel workflow-panel">
        <div className="panel-heading"><div><p className="eyebrow">LIVE WORKFLOW</p><h2>Orders by production stage</h2></div><span className="live"><i/>Live</span></div>
        <div className="workflow">
          {steps.map((step, i) => <div className="step-wrap" key={step.id}>
            <button className={`step-card ${stepFilter === String(step.id) ? 'selected' : ''}`} onClick={() => setStepFilter(stepFilter === String(step.id) ? 'all' : String(step.id))}>
              <span className="step-number" style={{background: step.color}}>{String(i + 1).padStart(2, '0')}</span>
              <span><small>{step.name}</small><strong>{dashboard?.by_step.find(s => s.step === step.name)?.count || 0} orders</strong></span>
            </button>{i < steps.length - 1 && <ChevronRight className="flow-arrow"/>}
          </div>)}
        </div>
      </section>

      <div className="content-grid">
        <section id="orders" className="panel orders-panel">
          <div className="panel-heading orders-heading"><div><p className="eyebrow">WORK QUEUE</p><h2>Active orders</h2></div><div className="search"><Search size={17}/><input aria-label="Search orders" placeholder="Search orders..." value={query} onChange={e => setQuery(e.target.value)}/>{stepFilter !== 'all' && <button onClick={() => setStepFilter('all')}><X size={14}/> Clear</button>}</div></div>
          <div className="table-wrap"><table><thead><tr><th>Order</th><th>Customer</th><th>Stage</th><th>Qty</th><th>Priority</th><th/></tr></thead><tbody>
            {visibleOrders.map(order => <tr key={order.id}><td><strong>{order.code}</strong><small>{order.product}</small></td><td>{order.customer}</td><td>{order.current_step ? <span className="stage"><i style={{background: order.current_step.color}}/>{order.current_step.name}</span> : <span className="complete-pill"><Check size={13}/>Completed</span>}</td><td>{order.quantity.toLocaleString()}</td><td><span className={`priority ${order.priority}`}>{priorityLabel[order.priority]}</span></td><td>{order.status === 'active' && <button className="icon-action" title="Advance order" onClick={() => setModal(order)}><ArrowRight size={17}/></button>}</td></tr>)}
            {!visibleOrders.length && <tr><td colSpan="6" className="empty">No orders match this view.</td></tr>}
          </tbody></table></div>
        </section>

        <section id="resources" className="panel resource-panel">
          <div className="panel-heading"><div><p className="eyebrow">CAPACITY</p><h2>Resource usage</h2></div></div>
          <div className="resource-list">{dashboard?.resource_usage.map(resource => {
            const pct = Math.min(100, Math.round(resource.used / resource.capacity * 100))
            return <div className="resource" key={resource.name}><div><strong>{resource.name}</strong><span>{resource.used.toLocaleString()} / {resource.capacity.toLocaleString()} {resource.unit}</span></div><div className="bar"><i style={{width: `${pct}%`}}/></div><small>{pct}%</small></div>
          })}</div>
        </section>
      </div>

      <footer>Prototype manufacturing control system <span>•</span> Last synced just now</footer>
    </main>

    {modal === 'create' && <Modal title="Create production order" subtitle="The order will start at Material Prep." close={() => setModal(null)}>
      <form onSubmit={createOrder} className="form">
        <label>Product name<input required minLength="2" placeholder="e.g. Custom cranial plate" value={form.product} onChange={e => setForm({...form, product: e.target.value})}/></label>
        <label>Customer<input required minLength="2" placeholder="Hospital or laboratory" value={form.customer} onChange={e => setForm({...form, customer: e.target.value})}/></label>
        <div className="form-row"><label>Quantity<input required type="number" min="1" value={form.quantity} onChange={e => setForm({...form, quantity: e.target.value})}/></label><label>Priority<select value={form.priority} onChange={e => setForm({...form, priority: e.target.value})}><option value="normal">Normal</option><option value="high">High</option><option value="urgent">Urgent</option></select></label></div>
        <div className="modal-actions"><button type="button" className="secondary" onClick={() => setModal(null)}>Cancel</button><button className="primary" disabled={busy}>{busy ? 'Creating...' : 'Create order'}</button></div>
      </form>
    </Modal>}

    {modal?.id && <Modal title={`Advance ${modal.code}`} subtitle={`${modal.current_step?.name} → ${nextStepName(modal, steps)}`} close={() => setModal(null)}>
      <div className="advance-summary"><span style={{background: modal.current_step?.color}}>{modal.current_step?.name}</span><ArrowRight/><span>{nextStepName(modal, steps)}</span></div>
      <p className="field-intro">Record resources consumed in this stage <em>(optional)</em></p>
      <div className="usage-grid">{resources.map(resource => <label key={resource.id}><span>{resource.name}<small>{resource.unit}</small></span><input type="number" min="0" step="0.1" placeholder="0" value={usage[resource.id] || ''} onChange={e => setUsage({...usage, [resource.id]: e.target.value})}/></label>)}</div>
      <div className="modal-actions"><button className="secondary" onClick={() => setModal(null)}>Cancel</button><button className="primary" disabled={busy} onClick={advanceOrder}>{busy ? 'Updating...' : `Move to ${nextStepName(modal, steps)}`}</button></div>
    </Modal>}
  </div>
}

function nextStepName(order, steps) {
  const next = steps.find(step => step.sequence > order.current_step?.sequence)
  return next?.name || 'Complete order'
}

function Metric({icon, label, value, note, accent, warning}) {
  return <article className={`metric ${accent ? 'accent' : ''} ${warning ? 'warning' : ''}`}><span className="metric-icon">{icon}</span><div><small>{label}</small><strong>{value}</strong><p>{note}</p></div></article>
}

function Modal({title, subtitle, close, children}) {
  return <div className="modal-backdrop" onMouseDown={e => e.target === e.currentTarget && close()}><section className="modal"><button className="modal-close" onClick={close}><X/></button><p className="eyebrow">PRODUCTION WORKFLOW</p><h2>{title}</h2><p className="modal-subtitle">{subtitle}</p>{children}</section></div>
}

export default App

