import React, { useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Outlet, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import {
  Activity,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  Clock3,
  ExternalLink,
  FolderKanban,
  Github,
  LayoutDashboard,
  Menu,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react';
import { applyApproval, getApproval, getCandidate, getCandidates, getPortfolioHealth, getPortfolioRanking, getProjects, getPublishedProjects, sendCandidateEmail, syncGitHub } from '../services/api';
import './AdminApp.css';

const navItems = [
  { label: 'Dashboard', path: '/admin', icon: LayoutDashboard, end: true },
  { label: 'Candidates', path: '/admin/candidates', icon: Users },
  { label: 'Portfolio', path: '/admin/portfolio', icon: FolderKanban },
  { label: 'GitHub', path: '/admin/github', icon: Github },
  { label: 'Activity', path: '/admin/activity', icon: Activity },
  { label: 'Settings', path: '/admin/settings', icon: Settings },
];

const formatDate = (value) => value ? new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value)) : 'Not recorded';
const scoreValue = (value) => Number.isFinite(Number(value)) ? Math.round(Number(value)) : '--';
const titleCase = (value = '') => value.toLowerCase().replace(/(^|[_-])\w/g, (letter) => letter.toUpperCase()).replace(/_/g, ' ');

function useResource(loader, dependencies = []) {
  const [state, setState] = useState({ data: null, loading: true, error: '' });
  const reload = async () => {
    setState({ data: null, loading: true, error: '' });
    try {
      setState({ data: await loader(), loading: false, error: '' });
    } catch (error) {
      setState({ data: null, loading: false, error: error.message });
    }
  };
  useEffect(() => { reload(); }, dependencies);
  return { ...state, reload };
}

function StatusBadge({ value = 'REVIEW' }) {
  const normalized = value.toUpperCase();
  return <span className={`admin-badge badge-${normalized.toLowerCase()}`}>{titleCase(normalized)}</span>;
}

function MetricCard({ label, value, icon: Icon, tone = 'lime', detail }) {
  return <article className={`metric-card metric-${tone}`}>
    <div className="metric-icon"><Icon size={18} /></div>
    <div><p>{label}</p><strong>{value}</strong>{detail && <small>{detail}</small>}</div>
  </article>;
}

function EmptyState({ title, message, icon: Icon = FolderKanban }) {
  return <div className="admin-empty"><Icon size={28} /><h3>{title}</h3><p>{message}</p></div>;
}

function ErrorState({ message, onRetry }) {
  return <div className="admin-error"><CircleAlert size={22} /><div><strong>Could not load this view</strong><p>{message}</p></div>{onRetry && <button className="admin-button button-muted" onClick={onRetry}>Retry</button>}</div>;
}

function LoadingState({ label = 'Loading intelligence' }) {
  return <div className="admin-loading"><RefreshCw size={20} className="spin" /> {label}...</div>;
}

function ScoreBar({ label, value, accent = false }) {
  const score = Number(value) || 0;
  return <div className={`score-row ${accent ? 'score-row-accent' : ''}`}><div><span>{label}</span><strong>{scoreValue(value)}</strong></div><div className="score-track"><span style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div></div>;
}

function CandidateCard({ candidate, project }) {
  const score = candidate.overall_score ?? project?.overall_score;
  const recommendation = candidate.recommendation || project?.recommendation || 'REVIEW';
  const repoUrl = candidate.github_url || candidate.repository_url || project?.github_url;
  return <Link className="candidate-card" to={`/admin/candidates/${candidate.candidate_id}`}>
    <div className="candidate-card-top"><div><span className="eyebrow">{candidate.full_name || project?.full_name || 'Repository'}</span><h3>{candidate.suggested_title || candidate.repository_name || project?.repository_name || 'Untitled project'}</h3></div><StatusBadge value={recommendation} /></div>
    <p className="candidate-description">{candidate.suggested_description || candidate.description || project?.description || 'No project description has been recorded yet.'}</p>
    <div className="candidate-stat-grid"><div><small>Overall score</small><strong>{scoreValue(score)}</strong></div><div><small>Priority</small><strong>{scoreValue(candidate.candidate_priority)}</strong></div><div><small>Portfolio fit</small><strong>{scoreValue(candidate.portfolio_fit_score)}</strong></div><div><small>Duplicate risk</small><strong>{candidate.duplicate_risk || 'Unknown'}</strong></div></div>
    <div className="candidate-card-foot"><span>{formatDate(candidate.date_analyzed || candidate.updated_at || candidate.created_at)}</span>{repoUrl && <span className="inline-link"><ExternalLink size={13} /> GitHub</span>}<ChevronRight size={16} /></div>
  </Link>;
}

function AdminShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  return <div className="admin-app"><aside className={`admin-sidebar ${mobileOpen ? 'is-open' : ''}`}>
    <div className="admin-brand"><div className="brand-mark"><Sparkles size={17} /></div><div><strong>Portfolio</strong><span>Command Center</span></div><button className="sidebar-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={19} /></button></div>
    <div className="sidebar-label">Workspace</div><nav className="admin-nav">{navItems.map(({ label, path, icon: Icon, end }) => <NavLink key={path} to={path} end={end} onClick={() => setMobileOpen(false)} className={({ isActive }) => isActive ? 'admin-nav-link active' : 'admin-nav-link'}><Icon size={18} /><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-foot"><ShieldCheck size={16} /><span>Private workspace<br /><small>Authentication boundary reserved</small></span></div>
  </aside>{mobileOpen && <button className="admin-overlay" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}
    <main className="admin-main"><header className="admin-topbar"><button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21} /></button><div><p className="admin-kicker">Private admin area</p><h1>Portfolio intelligence</h1></div><Link className="public-link" to="/"><ArrowLeft size={15} /> View public portfolio</Link></header><div className="admin-content"><Outlet /></div></main>
  </div>;
}

function Dashboard() {
  const projects = useResource(getProjects);
  const candidates = useResource(getCandidates);
  const projectList = projects.data || [];
  const candidateList = candidates.data || [];
  const recentCandidates = candidateList.slice().sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)).slice(0, 4);
  const analyzed = projectList.filter((project) => project.analysis_status === 'ANALYZED').length;
  const review = projectList.filter((project) => (project.recommendation || '').toUpperCase() === 'REVIEW').length;
  const ignored = projectList.filter((project) => (project.recommendation || '').toUpperCase() === 'IGNORE').length;
  const featured = projectList.filter((project) => (project.portfolio_status || '').toUpperCase() === 'FEATURED').length;
  if (projects.loading || candidates.loading) return <LoadingState label="Loading dashboard" />;
  if (projects.error && candidates.error) return <ErrorState message={projects.error} onRetry={() => { projects.reload(); candidates.reload(); }} />;
  return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Overview / September 2026</p><h2>Good morning, Pratham.</h2><p>Review the signal behind your repositories and decide what deserves a place in the portfolio.</p></div><Link className="admin-button button-primary" to="/admin/candidates"><Users size={16} /> Review candidates</Link></section>
    <section className="metric-grid"><MetricCard label="Projects discovered" value={projectList.length} icon={Github} detail="From GitHub sync" /><MetricCard label="Projects analyzed" value={analyzed} icon={BarChart3} tone="blue" detail={`${projectList.length ? Math.round((analyzed / projectList.length) * 100) : 0}% of discovery`} /><MetricCard label="Candidates" value={candidateList.length} icon={Sparkles} tone="amber" detail="Pipeline records" /><MetricCard label="Needs review" value={review} icon={Clock3} tone="coral" detail={`${ignored} ignored · ${featured} featured`} /></section>
    <section className="section-heading"><div><p className="admin-kicker">Latest signal</p><h2>Recent candidates</h2></div><Link to="/admin/candidates" className="text-link">View all <ChevronRight size={15} /></Link></section>
    {recentCandidates.length ? <div className="candidate-grid">{recentCandidates.map((candidate) => <CandidateCard key={candidate.candidate_id} candidate={candidate} project={projectList.find((project) => project.github_repo_id === candidate.github_repo_id)} />)}</div> : <EmptyState title="No candidates yet" message="Run a GitHub sync and project evaluation to start building the candidate pipeline." icon={Sparkles} />}
  </div>;
}

function CandidatesPage() {
  const candidates = useResource(getCandidates);
  const projects = useResource(getProjects);
  const [filter, setFilter] = useState('ALL');
  const [sort, setSort] = useState('priority');
  const items = useMemo(() => {
    const filtered = (candidates.data || []).filter((candidate) => filter === 'ALL' || candidate.candidate_status === filter || candidate.recommendation === filter);
    return filtered.sort((a, b) => {
      if (sort === 'score') return (b.overall_score || 0) - (a.overall_score || 0);
      if (sort === 'oldest') return new Date(a.created_at) - new Date(b.created_at);
      if (sort === 'newest') return new Date(b.created_at) - new Date(a.created_at);
      return (b.candidate_priority || b.overall_score || 0) - (a.candidate_priority || a.overall_score || 0);
    });
  }, [candidates.data, filter, sort]);
  if (candidates.loading || projects.loading) return <LoadingState label="Loading candidates" />;
  if (candidates.error) return <ErrorState message={candidates.error} onRetry={candidates.reload} />;
  return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Pipeline / Candidate review</p><h2>Candidate queue</h2><p>Inspect promising work before it reaches a future publishing workflow.</p></div><span className="record-count">{items.length} records</span></section><div className="toolbar"><div className="filter-tabs">{['ALL', 'CANDIDATE', 'REVIEW', 'REJECTED', 'FEATURED'].map((item) => <button key={item} className={filter === item ? 'filter-tab active' : 'filter-tab'} onClick={() => setFilter(item)}>{titleCase(item)}</button>)}</div><label className="sort-select">Sort by<select value={sort} onChange={(event) => setSort(event.target.value)}><option value="priority">Priority</option><option value="score">Overall score</option><option value="newest">Newest</option><option value="oldest">Oldest</option></select></label></div>{items.length ? <div className="candidate-grid">{items.map((candidate) => <CandidateCard key={candidate.candidate_id} candidate={candidate} project={(projects.data || []).find((project) => project.github_repo_id === candidate.github_repo_id)} />)}</div> : <EmptyState title="No matching candidates" message="There are no records in this view yet. Try another filter or run a sync." icon={Search} />}</div>;
}

function CandidateDetail() {
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const candidate = useResource(() => getCandidate(candidateId), [candidateId]);
  const projects = useResource(getProjects);
  const [reviewLater, setReviewLater] = useState(false);
  const [emailState, setEmailState] = useState({ status: 'idle', message: '' });
  if (candidate.loading || projects.loading) return <LoadingState label="Loading candidate" />;
  if (candidate.error) return <ErrorState message={candidate.error} onRetry={candidate.reload} />;
  const item = candidate.data;
  const project = (projects.data || []).find((entry) => entry.github_repo_id === item.github_repo_id) || {};
  const analysis = project.analysis || item.ai_analysis || {};
  const scores = analysis.scores || {};
  const recommendation = item.recommendation || project.recommendation || 'REVIEW';
  const list = (value) => Array.isArray(value) ? value : [];
  const handleEmail = async () => {
    setEmailState({ status: 'loading', message: '' });
    try {
      const result = await sendCandidateEmail(item.candidate_id);
      setEmailState({ status: result.status === 'already_sent' ? 'sent' : 'sent', message: result.status === 'already_sent' ? 'Approval email was already sent.' : 'Approval email sent.' });
    } catch (error) {
      setEmailState({ status: 'error', message: error.message });
    }
  };
  return <div className="page-stack"><button className="back-link" onClick={() => navigate('/admin/candidates')}><ArrowLeft size={15} /> Back to candidates</button><section className="detail-hero"><div><p className="admin-kicker">Candidate detail</p><div className="detail-title"><h2>{item.suggested_title || item.repository_name || project.repository_name}</h2><StatusBadge value={recommendation} /></div><p>{item.suggested_description || item.description || project.description || 'No description recorded.'}</p></div><div className="detail-actions"><button className="admin-button button-primary" onClick={handleEmail} disabled={emailState.status === 'loading' || emailState.status === 'sent'}><RefreshCw size={16} className={emailState.status === 'loading' ? 'spin' : ''} /> {emailState.status === 'loading' ? 'Sending...' : emailState.status === 'sent' ? 'Email sent' : 'Send approval email'}</button><button className="admin-button button-outline" disabled>Approve <span>Email link only</span></button><button className="admin-button button-outline" disabled>Reject <span>Email link only</span></button><button className={`admin-button ${reviewLater ? 'button-primary' : 'button-muted'}`} onClick={() => setReviewLater(true)}>{reviewLater ? <CheckCircle2 size={16} /> : <Clock3 size={16} />} {reviewLater ? 'Saved for later' : 'Review later'}</button></div>{emailState.message && <div className={emailState.status === 'error' ? 'email-feedback email-feedback-error' : 'email-feedback'}>{emailState.message}</div>}</section>
    <div className="detail-layout"><div className="detail-main"><section className="detail-section"><div className="section-heading compact"><h3>Project</h3>{(item.github_url || item.repository_url || project.github_url) && <a className="text-link" href={item.github_url || item.repository_url || project.github_url} target="_blank" rel="noreferrer">Open on GitHub <ExternalLink size={14} /></a>}</div><div className="meta-grid"><Meta label="Repository" value={item.full_name || project.full_name || item.repository_name} /><Meta label="Languages" value={(item.languages || project.languages || []).join(', ') || 'Not recorded'} /><Meta label="Topics" value={(item.topics || project.topics || []).join(', ') || 'Not recorded'} /><Meta label="Collaborators" value={(item.collaborators || project.contributors || []).join(', ') || 'Not recorded'} /><Meta label="Stars" value={project.stars ?? 'Not recorded'} /><Meta label="Forks" value={project.forks ?? 'Not recorded'} /></div></section><section className="detail-section"><div className="section-heading compact"><h3>AI analysis</h3><span className="subtle-label">{item.analysis_version || project.analysis_version || 'phase2-v1'}</span></div><p className="analysis-summary">{analysis.summary || 'No analysis summary is available yet.'}</p><div className="analysis-columns"><InfoList label="Strengths" items={list(item.strengths || analysis.strengths)} /><InfoList label="Weaknesses" items={list(item.weaknesses || analysis.weaknesses)} /><InfoList label="Evidence" items={list(item.evidence || analysis.evidence)} /><InfoList label="Missing evidence" items={list(item.missing_evidence || analysis.missing_evidence)} /><InfoList label="Why it stands out" items={list(item.why_it_stands_out || analysis.why_it_stands_out)} /></div></section></div><aside className="detail-side"><section className="score-panel"><div className="section-heading compact"><h3>Scores</h3><span className="score-total">{scoreValue(item.overall_score ?? project.overall_score)}</span></div>{[['Technical Depth', 'technical_depth'], ['Complexity', 'complexity'], ['Originality', 'originality'], ['Impact', 'impact'], ['Engineering Quality', 'engineering_quality'], ['Maturity', 'maturity'], ['Collaboration', 'collaboration'], ['Portfolio Fit', 'portfolio_fit']].map(([label, key]) => <ScoreBar key={key} label={label} value={scores[key]} accent={key === 'portfolio_fit'} />)}</section><section className="intelligence-panel"><div className="section-heading compact"><h3>Portfolio intelligence</h3><Sparkles size={17} /></div><Meta label="Duplicate risk" value={item.duplicate_risk || 'Not recorded'} /><Meta label="Portfolio differentiation" value={item.differentiation_reason || 'Not recorded'} /><Meta label="Candidate priority" value={scoreValue(item.candidate_priority)} /><Meta label="Quality gate" value={recommendation} /></section></aside></div></div>;
}

function Meta({ label, value }) { return <div className="meta-item"><span>{label}</span><strong>{value || 'Not recorded'}</strong></div>; }
function InfoList({ label, items }) { return <div className="info-list"><h4>{label}</h4>{items.length ? <ul>{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p>Not recorded</p>}</div>; }

function PortfolioPage() {
  const projects = useResource(getProjects);
  const published = useResource(getPublishedProjects);
  const candidates = useResource(getCandidates);
  const ranking = useResource(getPortfolioRanking);
  const health = useResource(getPortfolioHealth);
  if (projects.loading || published.loading || candidates.loading || ranking.loading || health.loading) return <LoadingState label="Loading portfolio" />;
  if (projects.error || published.error || candidates.error) return <ErrorState message="Portfolio representation is unavailable." onRetry={() => { projects.reload(); published.reload(); candidates.reload(); ranking.reload(); health.reload(); }} />;
  const publishedItems = published.data || [];
  const publishedIds = new Set(publishedItems.map((item) => item.github_repo_id));
  const approvedItems = (candidates.data || []).filter((item) => item.candidate_status === 'APPROVED' && !publishedIds.has(item.github_repo_id));
  const legacyItems = publishedItems.filter((item) => item.source === 'LEGACY');
  const groups = [
    ['PUBLISHED', 'Published', publishedItems.filter((item) => item.source !== 'LEGACY')],
    ['APPROVED', 'Approved / unpublished', approvedItems],
    ['LEGACY', 'Legacy', legacyItems],
  ];
  return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Portfolio / Publishing view</p><h2>Portfolio representation</h2><p>A read-only view of published projects, approved projects awaiting publication, and legacy records. Public portfolio data is not edited here.</p></div></section><section className="ranking-health"><div className="health-card"><div className="section-heading compact"><div><p className="admin-kicker">Portfolio health</p><h3>{health.data?.health_score ?? '--'} <span>/ 100</span></h3></div><BarChart3 size={19} /></div><div className="health-metrics"><Meta label="Breadth" value={health.data?.breadth_score ?? '--'} /><Meta label="Depth" value={health.data?.depth_score ?? '--'} /><Meta label="Diversity" value={health.data?.diversity_score ?? '--'} /><Meta label="Redundancy" value={health.data?.redundancy_score ?? '--'} /></div>{health.data?.recommendations?.length ? <ul className="health-recommendations">{health.data.recommendations.map((recommendation) => <li key={recommendation}>{recommendation}</li>)}</ul> : <p className="inline-empty">No portfolio health recommendations.</p>}</div><div className="ranking-card"><div className="section-heading compact"><div><p className="admin-kicker">Advisory ranking</p><h3>Portfolio Ranking</h3></div><span className="record-count">Max featured: {ranking.data?.max_featured_projects ?? '--'}</span></div>{ranking.data?.ranked_projects?.length ? <div className="ranking-list">{ranking.data.ranked_projects.slice(0, 8).map((item) => <div className="ranking-row" key={item.github_repo_id}><strong>#{item.rank}</strong><div><b>{item.title}</b><span>{item.explanation}</span></div><em>{item.ranking_score}</em></div>)}</div> : <div className="inline-empty">No eligible projects to rank.</div>}</div></section>{groups.map(([status, label, group]) => <section className="portfolio-group" key={status}><div className="section-heading compact"><div><h3>{label}</h3><p>{status === 'PUBLISHED' ? 'Visible through the public portfolio API' : status === 'APPROVED' ? 'Approved but not yet represented publicly' : 'Preserved historical portfolio records'}</p></div><StatusBadge value={status} /></div>{group.length ? <div className="portfolio-list">{group.map((project) => <div className="portfolio-row" key={project.github_repo_id || project.candidate_id}><div className="portfolio-dot" /><div><strong>{project.title || project.suggested_title || project.repository_name || project.full_name}</strong><span>{project.description || project.suggested_description || 'No description recorded.'}</span></div><span className="portfolio-score">{status === 'PUBLISHED' ? `#${project.display_order}` : titleCase(status)}</span></div>)}</div> : <div className="inline-empty">No records in this category.</div>}</section>)}</div>;
}

function GitHubPage() {
  const [state, setState] = useState({ status: 'idle', data: null, error: '' });
  const sync = async () => { setState({ status: 'loading', data: null, error: '' }); try { setState({ status: 'success', data: await syncGitHub(), error: '' }); } catch (error) { setState({ status: 'error', data: null, error: error.message }); } };
  return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Integrations / Source</p><h2>GitHub connection</h2><p>Keep repository discovery current. Credentials remain server-side and are never displayed here.</p></div><button className="admin-button button-primary" onClick={sync} disabled={state.status === 'loading'}><RefreshCw size={16} className={state.status === 'loading' ? 'spin' : ''} /> {state.status === 'loading' ? 'Syncing...' : 'Sync GitHub'}</button></section><section className="github-summary"><div className="connection-orb"><Github size={27} /></div><div><span className="eyebrow">Connected account</span><h3>Configured on backend</h3><p>The connected username and token are intentionally not exposed by the current API.</p></div><span className="connection-status"><span /> Ready to sync</span></section>{state.status === 'success' && <div className="success-state"><CheckCircle2 size={19} /><span>Sync complete: {state.data.repositories_upserted} repositories updated, {state.data.repositories_skipped} skipped.</span></div>}{state.status === 'error' && <ErrorState message={state.error} />}</div>;
}

function ActivityPage() { return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Workspace / Audit trail</p><h2>Activity</h2><p>A calm record of the system events that matter to review.</p></div></section><EmptyState title="Activity will appear here" message="The backend does not expose activity events yet. This view is reserved for a future audit trail and will not invent records." icon={Activity} /></div>; }
function SettingsPage() { return <div className="page-stack"><section className="page-heading"><div><p className="admin-kicker">Workspace / Read-only configuration</p><h2>Settings</h2><p>Safe configuration signals for the current analysis engine. Secrets and credentials are never rendered in the browser.</p></div></section><div className="settings-grid"><section className="settings-card"><div className="section-heading compact"><h3>AI provider</h3><span className="settings-readonly">Read-only</span></div><Meta label="Provider" value="Ollama" /><Meta label="Model" value="Server-managed" /><Meta label="Analysis version" value="phase2-v1" /></section><section className="settings-card"><div className="section-heading compact"><h3>Quality thresholds</h3><span className="settings-readonly">Server-managed</span></div><Meta label="Ignore maximum" value="64" /><Meta label="Candidate minimum" value="85" /><Meta label="Quality gate" value="Deterministic" /></section><section className="settings-card"><div className="section-heading compact"><h3>Scoring configuration</h3><span className="settings-readonly">Server-managed</span></div>{[['Technical depth', '20%'], ['Complexity', '15%'], ['Originality', '15%'], ['Impact', '15%'], ['Engineering quality', '15%'], ['Maturity', '10%'], ['Collaboration', '5%'], ['Portfolio fit', '5%']].map(([label, value]) => <Meta key={label} label={label} value={value} />)}</section></div></div>; }

export function ApprovalResult() {
  const { token } = useParams();
  const [state, setState] = useState({ status: 'loading', name: '', action: '', message: '' });
  useEffect(() => {
    let active = true;
    const process = async () => {
      try {
        const preview = await getApproval(token);
        const result = await applyApproval(token, preview.action);
        if (active) setState({ status: result.status === 'already_processed' ? 'already_processed' : 'success', name: result.candidate_name, action: result.decision, message: '' });
      } catch (error) {
        if (active) setState({ status: error.message.includes('expired') ? 'expired' : 'error', name: '', action: '', message: error.message });
      }
    };
    process();
    return () => { active = false; };
  }, [token]);
  if (state.status === 'loading') return <div className="approval-page"><div className="approval-card"><RefreshCw className="spin" size={25} /><p>Checking your approval link...</p></div></div>;
  const heading = state.status === 'success' ? state.action === 'APPROVED' ? 'Approved' : state.action === 'REJECTED' ? 'Rejected' : 'Review later' : state.status === 'already_processed' ? 'Already processed' : state.status === 'expired' ? 'Link expired' : 'Link unavailable';
  const message = state.status === 'success' ? `${state.name} has been ${state.action === 'APPROVED' ? 'approved for future portfolio publication' : state.action === 'REJECTED' ? 'rejected and will not be added' : 'marked for later review'}.` : state.status === 'already_processed' ? 'This decision has already been processed.' : state.status === 'expired' ? 'This approval link has expired.' : 'This approval link is invalid or unavailable.';
  return <div className={`approval-page approval-${state.status}`}><div className="approval-card"><div className="approval-symbol">{state.status === 'success' ? <CheckCircle2 size={28} /> : <CircleAlert size={28} />}</div><p className="admin-kicker">Portfolio decision</p><h1>{heading}</h1><p>{message}</p><Link className="admin-button button-primary" to="/admin">Return to command center</Link></div></div>;
}

export default function AdminApp() { return <Routes><Route element={<AdminShell />}><Route index element={<Dashboard />} /><Route path="candidates" element={<CandidatesPage />} /><Route path="candidates/:candidateId" element={<CandidateDetail />} /><Route path="portfolio" element={<PortfolioPage />} /><Route path="github" element={<GitHubPage />} /><Route path="activity" element={<ActivityPage />} /><Route path="settings" element={<SettingsPage />} /></Route></Routes>; }
