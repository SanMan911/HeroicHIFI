import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Input } from "../components/ui/input";
import { motion } from "framer-motion";
import { LayoutDashboard, IndianRupee, Users, MessageSquare, RefreshCw, CheckCircle, Clock, XCircle, Eye, Download, Trash2, UserCog, MessageCircle, Ticket, Shield, Award, Package, AlertTriangle, PauseCircle, PlayCircle, Star, ArrowUpDown, CalendarDays, Activity, Plus } from "lucide-react";
import { toast } from "sonner";

const STATUS_COLORS = {
  pending: "bg-amber-100 text-amber-800 border-amber-200",
  confirmed: "bg-green-100 text-green-800 border-green-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  rejected: "bg-red-100 text-red-800 border-red-200",
  failed: "bg-red-100 text-red-800 border-red-200",
  open: "bg-blue-100 text-blue-800 border-blue-200",
  responded: "bg-cyan-100 text-cyan-800 border-cyan-200",
  closed: "bg-slate-100 text-slate-600 border-slate-200",
};

const ROLE_COLORS = {
  admin: "bg-blue-50 text-blue-700 border-blue-200",
  volunteer: "bg-green-50 text-green-700 border-green-200",
  member: "bg-slate-50 text-slate-600 border-slate-200",
};

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-2xl p-5 border border-sky-100 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 mb-1">{label}</p>
          <p className="text-2xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{value}</p>
          {sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}
        </div>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[status] || STATUS_COLORS.pending}`}>
      {status}
    </span>
  );
}

function DonationsTab({ donations, onStatusChange }) {
  const [expandedId, setExpandedId] = useState(null);
  if (!donations.length) return <p className="text-center text-slate-400 py-12">No donations yet.</p>;
  return (
    <div className="space-y-3" data-testid="admin-donations-list">
      {donations.map((d) => (
        <div key={d.id} className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden">
          <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30 transition-colors" onClick={() => setExpandedId(expandedId === d.id ? null : d.id)}>
            <div className="flex items-center gap-4 min-w-0">
              <div className="w-9 h-9 rounded-full bg-[#FF7F00]/10 flex items-center justify-center shrink-0"><IndianRupee className="w-4 h-4 text-[#FF7F00]" /></div>
              <div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{d.name}</p><p className="text-xs text-slate-400">{d.email}</p></div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-sm font-semibold text-[#0D2847]">{"\u20B9"}{d.amount?.toLocaleString("en-IN")}</span>
              <StatusBadge status={d.status} /><Eye className="w-4 h-4 text-slate-300" />
            </div>
          </div>
          {expandedId === d.id && (
            <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div><span className="text-slate-400">Phone:</span> <span className="text-slate-600">{d.phone}</span></div>
                <div><span className="text-slate-400">PAN:</span> <span className="text-slate-600">{d.pan_number || "—"}</span></div>
                <div><span className="text-slate-400">Aadhaar:</span> <span className="text-slate-600">{d.aadhaar_number || "—"}</span></div>
                <div><span className="text-slate-400">Date:</span> <span className="text-slate-600">{new Date(d.created_at).toLocaleDateString("en-IN")}</span></div>
                {d.address && <div className="col-span-2"><span className="text-slate-400">Address:</span> <span className="text-slate-600">{d.address}</span></div>}
                {d.razorpay_payment_id && <div className="col-span-2"><span className="text-slate-400">Payment ID:</span> <span className="text-slate-600 font-mono text-[10px]">{d.razorpay_payment_id}</span></div>}
              </div>
              {d.message && <p className="text-xs text-slate-500 italic">"{d.message}"</p>}
              <div className="flex items-center gap-2 pt-1 flex-wrap">
                <span className="text-xs text-slate-400">Update status:</span>
                <Select value={d.status} onValueChange={(val) => onStatusChange("donations", d.id, val)}>
                  <SelectTrigger className="h-7 text-xs w-32 rounded-lg" data-testid={`donation-status-${d.id}`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="rejected">Rejected</SelectItem></SelectContent>
                </Select>
                {d.pan_number && (
                  <a href={`${process.env.REACT_APP_BACKEND_URL}/api/donations/${d.id}/certificate`} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium bg-[#FF7F00]/10 text-[#FF7F00] hover:bg-[#FF7F00]/20 transition-colors" data-testid={`download-cert-${d.id}`}>
                    <Download className="w-3 h-3" /> 80G Certificate
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function QueriesTab({ queries, onStatusChange }) {
  const [expandedId, setExpandedId] = useState(null);
  if (!queries.length) return <p className="text-center text-slate-400 py-12">No queries yet.</p>;
  return (
    <div className="space-y-3" data-testid="admin-queries-list">
      {queries.map((q) => (
        <div key={q.id} className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden">
          <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30 transition-colors" onClick={() => setExpandedId(expandedId === q.id ? null : q.id)}>
            <div className="flex items-center gap-4 min-w-0">
              <div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0"><MessageSquare className="w-4 h-4 text-[#28A9E2]" /></div>
              <div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{q.subject}</p><p className="text-xs text-slate-400">{q.name} &middot; {q.mission}</p></div>
            </div>
            <div className="flex items-center gap-4 shrink-0"><StatusBadge status={q.status} /><Eye className="w-4 h-4 text-slate-300" /></div>
          </div>
          {expandedId === q.id && (
            <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><span className="text-slate-400">Email:</span> <span className="text-slate-600">{q.email}</span></div>
                <div><span className="text-slate-400">Date:</span> <span className="text-slate-600">{new Date(q.created_at).toLocaleDateString("en-IN")}</span></div>
              </div>
              <p className="text-xs text-slate-600 bg-sky-50/50 rounded-lg p-3">{q.message}</p>
              <div className="flex items-center gap-2 pt-1">
                <Select value={q.status} onValueChange={(val) => onStatusChange("queries", q.id, val)}>
                  <SelectTrigger className="h-7 text-xs w-32 rounded-lg" data-testid={`query-status-${q.id}`}><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="open">Open</SelectItem><SelectItem value="responded">Responded</SelectItem><SelectItem value="closed">Closed</SelectItem></SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { user, loading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].dashboard;
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [donations, setDonations] = useState([]);
  const [volunteers, setVolunteers] = useState([]);
  const [queries, setQueries] = useState([]);
  const [users, setUsers] = useState([]);
  const [messageThreads, setMessageThreads] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [wallOfFame, setWallOfFame] = useState([]);
  const [roleRequests, setRoleRequests] = useState([]);
  const [drives, setDrives] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);
  const [activeAdminThread, setActiveAdminThread] = useState(null);
  const [adminThreadMsgs, setAdminThreadMsgs] = useState([]);
  const [fetching, setFetching] = useState(true);
  const [roleFilter, setRoleFilter] = useState("all");
  const [myRoleRequests, setMyRoleRequests] = useState([]);
  const [roleRequestForm, setRoleRequestForm] = useState({ requested_role: "", reason: "" });

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!isAdmin) {
      try {
        const [reqRes, drivesRes] = await Promise.all([
          api.get("/role-requests/mine"),
          api.get("/drives"),
        ]);
        setMyRoleRequests(reqRes.data);
        setDrives(drivesRes.data);
      } catch {}
      setFetching(false);
      return;
    }
    setFetching(true);
    try {
      const [statsRes, donRes, volRes, qRes, usersRes, msgsRes, ticketsRes, wofRes, rrRes, drivesRes, logsRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/donations"),
        api.get("/admin/volunteers"),
        api.get("/admin/queries"),
        api.get("/admin/users"),
        api.get("/admin/messages"),
        api.get("/admin/tickets"),
        api.get("/wall-of-fame"),
        api.get("/admin/role-requests"),
        api.get("/drives"),
        api.get("/admin/activity-logs?limit=200"),
      ]);
      setStats(statsRes.data); setDonations(donRes.data); setVolunteers(volRes.data);
      setQueries(qRes.data); setUsers(usersRes.data); setMessageThreads(msgsRes.data);
      setTickets(ticketsRes.data); setWallOfFame(wofRes.data); setRoleRequests(rrRes.data);
      setDrives(drivesRes.data); setActivityLogs(logsRes.data);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setFetching(false); }
  }, [isAdmin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (collection, itemId, newStatus) => {
    try { await api.put(`/admin/${collection}/${itemId}/status`, { status: newStatus }); toast.success(`Status updated to "${newStatus}"`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleDeleteUser = async (email) => {
    if (!window.confirm(`Delete user "${email}"? This cannot be undone.`)) return;
    try { await api.delete(`/admin/users/${encodeURIComponent(email)}`); toast.success(`User ${email} deleted`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const loadAdminThread = async (email1, email2, senderName, recipientName) => {
    try { const { data } = await api.get(`/admin/messages/thread/${encodeURIComponent(email1)}/${encodeURIComponent(email2)}`); setAdminThreadMsgs(data); setActiveAdminThread({ email1, email2, senderName, recipientName }); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleAdminUpdateUser = async (email, updates) => {
    try { await api.put(`/admin/users/${encodeURIComponent(email)}/update`, updates); toast.success(`User ${email} updated`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleAddBadge = async (email, badge) => {
    try { await api.post(`/admin/users/${encodeURIComponent(email)}/badge`, { badge }); toast.success(`Badge "${badge}" added`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleRemoveBadge = async (email, badge) => {
    try { await api.delete(`/admin/users/${encodeURIComponent(email)}/badge/${encodeURIComponent(badge)}`); toast.success(`Badge "${badge}" removed`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleTicketStatusChange = async (ticketId, status) => {
    try { await api.put(`/admin/tickets/${ticketId}/status`, { status }); toast.success("Ticket status updated"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleTicketRespond = async (ticketId, response) => {
    if (!response) return;
    try { await api.put(`/admin/tickets/${ticketId}/respond`, { response }); toast.success("Response sent"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleToggleWallOfFame = async (email, isOnWall) => {
    try {
      if (isOnWall) { await api.delete(`/admin/wall-of-fame/${encodeURIComponent(email)}`); toast.success("Removed from Wall of Fame"); }
      else { await api.post(`/admin/wall-of-fame/${encodeURIComponent(email)}`); toast.success("Added to Wall of Fame!"); }
      fetchData();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleRoleRequestAction = async (requestId, action) => {
    try { await api.put(`/admin/role-requests/${requestId}/${action}`); toast.success(`Request ${action}d`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleSubmitRoleRequest = async () => {
    if (!roleRequestForm.requested_role) { toast.error("Select a role"); return; }
    try { await api.post("/role-requests", roleRequestForm); toast.success("Role change request submitted!"); setRoleRequestForm({ requested_role: "", reason: "" }); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail, err)); }
  };

  // Drive management
  const [driveForm, setDriveForm] = useState({ title: "", description: "", date: "", location: "", drive_type: "upcoming", image_url: "" });
  const [showDriveForm, setShowDriveForm] = useState(false);
  const handleCreateDrive = async () => {
    if (!driveForm.title || !driveForm.date || !driveForm.location) { toast.error("Fill in title, date, and location"); return; }
    try { await api.post("/admin/drives", driveForm); toast.success("Drive created!"); setDriveForm({ title: "", description: "", date: "", location: "", drive_type: "upcoming", image_url: "" }); setShowDriveForm(false); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const handleDeleteDrive = async (driveId) => {
    if (!window.confirm("Delete this drive?")) return;
    try { await api.delete(`/admin/drives/${driveId}`); toast.success("Drive deleted"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-400">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  // ── Non-Admin Dashboard ──
  if (!isAdmin) {
    const upcomingDrives = drives.filter(d => d.drive_type === "upcoming");
    const pastDrives = drives.filter(d => d.drive_type === "past");
    return (
      <div className="min-h-screen py-12" data-testid="dashboard-page">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center"><LayoutDashboard className="w-6 h-6 text-[#1E56A0]" /></div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">{t.title}</h1>
                <p className="text-sm text-slate-500">{t.welcome}, {user.name || user.email} <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ml-2 ${ROLE_COLORS[user.role] || ROLE_COLORS.member}`}>{user.role}</span></p>
              </div>
            </div>

            {/* Role Change Request */}
            <div className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm" data-testid="role-change-section">
              <h2 className="text-lg font-semibold text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}><ArrowUpDown className="w-5 h-5 text-[#1E56A0]" /> Request Role Change</h2>
              {myRoleRequests.some(r => r.status === "pending") ? (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">You have a pending role change request. Please wait for admin review.</div>
              ) : (
                <div className="flex flex-col sm:flex-row gap-3">
                  <Select value={roleRequestForm.requested_role} onValueChange={(val) => setRoleRequestForm({ ...roleRequestForm, requested_role: val })}>
                    <SelectTrigger className="w-48 rounded-xl" data-testid="role-request-select"><SelectValue placeholder="Select new role..." /></SelectTrigger>
                    <SelectContent>
                      {user.role !== "volunteer" && <SelectItem value="volunteer">Volunteer</SelectItem>}
                      {user.role !== "member" && <SelectItem value="member">Member</SelectItem>}
                    </SelectContent>
                  </Select>
                  <Input placeholder="Reason (optional)" value={roleRequestForm.reason} onChange={(e) => setRoleRequestForm({ ...roleRequestForm, reason: e.target.value })} className="flex-1 rounded-xl" data-testid="role-request-reason" />
                  <Button onClick={handleSubmitRoleRequest} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="role-request-submit">Submit Request</Button>
                </div>
              )}
              {myRoleRequests.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs text-slate-500 font-medium">Your past requests:</p>
                  {myRoleRequests.map(r => (
                    <div key={r.id} className="flex items-center justify-between text-xs bg-sky-50/50 rounded-lg p-2">
                      <span>{r.current_role} &rarr; {r.requested_role}</span>
                      <StatusBadge status={r.status} />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Drives */}
            {upcomingDrives.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm" data-testid="upcoming-drives">
                <h2 className="text-lg font-semibold text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}><CalendarDays className="w-5 h-5 text-green-600" /> Upcoming Drives</h2>
                <div className="space-y-3">
                  {upcomingDrives.map(d => (
                    <div key={d.id} className="border border-green-100 rounded-xl p-4 bg-green-50/30">
                      <p className="text-sm font-semibold text-[#0D2847]">{d.title}</p>
                      <p className="text-xs text-slate-500 mt-1">{d.description}</p>
                      <div className="flex gap-4 mt-2 text-xs text-slate-400">
                        <span>{new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
                        <span>{d.location}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {pastDrives.length > 0 && (
              <div className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm" data-testid="past-drives">
                <h2 className="text-lg font-semibold text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}><CalendarDays className="w-5 h-5 text-slate-400" /> Past Drives</h2>
                <div className="space-y-3">
                  {pastDrives.map(d => (
                    <div key={d.id} className="border border-slate-100 rounded-xl p-4 bg-slate-50/30">
                      <p className="text-sm font-semibold text-[#0D2847]">{d.title}</p>
                      <p className="text-xs text-slate-500 mt-1">{d.description}</p>
                      <div className="flex gap-4 mt-2 text-xs text-slate-400">
                        <span>{new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
                        <span>{d.location}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    );
  }

  // ── Admin Dashboard ──
  const filteredUsers = roleFilter === "all" ? users : users.filter(u => u.role === roleFilter);
  const pendingRoleRequests = roleRequests.filter(r => r.status === "pending");

  const tabs = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "donations", label: "Donations", icon: IndianRupee, count: donations.length },
    { id: "roster", label: "Roster", icon: Users, count: users.length },
    { id: "role-requests", label: "Requests", icon: ArrowUpDown, count: pendingRoleRequests.length },
    { id: "drives", label: "Drives", icon: CalendarDays, count: drives.length },
    { id: "queries", label: "Queries", icon: MessageSquare, count: queries.length },
    { id: "messages", label: "Messages", icon: MessageCircle, count: messageThreads.length },
    { id: "tickets", label: "Tickets", icon: Ticket, count: tickets.length },
    { id: "activity", label: "Activity Log", icon: Activity },
  ];

  return (
    <div className="min-h-screen py-8" data-testid="dashboard-page">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center"><LayoutDashboard className="w-6 h-6 text-[#1E56A0]" /></div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">Admin Dashboard</h1>
                <p className="text-sm text-slate-500">{t.welcome}, {user.name || user.email}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetchData} disabled={fetching} className="rounded-full gap-2" data-testid="refresh-dashboard-btn">
              <RefreshCw className={`w-4 h-4 ${fetching ? "animate-spin" : ""}`} /> Refresh
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-white/80 rounded-2xl p-1.5 border border-sky-100 mb-8 overflow-x-auto" data-testid="dashboard-tabs">
            {tabs.map(({ id, label, icon: TabIcon, count }) => (
              <button key={id} onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap ${activeTab === id ? "bg-[#1E56A0] text-white shadow-sm" : "text-slate-500 hover:text-[#1E56A0] hover:bg-sky-50"}`}
                data-testid={`tab-${id}`}>
                <TabIcon className="w-4 h-4" />{label}
                {count !== undefined && count > 0 && <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${activeTab === id ? "bg-white/20" : "bg-sky-100 text-[#1E56A0]"}`}>{count}</span>}
              </button>
            ))}
          </div>

          {/* Overview */}
          {activeTab === "overview" && stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3" data-testid="admin-stats">
              <StatCard icon={IndianRupee} label="Donations" value={stats.donations.total} sub={`${"\u20B9"}${stats.donations.total_amount.toLocaleString("en-IN")}`} color="#FF7F00" />
              <StatCard icon={CheckCircle} label="Confirmed" value={stats.donations.confirmed} color="#16A34A" />
              <StatCard icon={Users} label="Volunteers" value={stats.volunteers?.total || 0} color="#1E56A0" />
              <StatCard icon={Users} label="Members" value={stats.members?.total || 0} color="#7C3AED" />
              <StatCard icon={ArrowUpDown} label="Pending Requests" value={stats.role_requests?.pending || 0} color="#F59E0B" />
              <StatCard icon={CalendarDays} label="Drives" value={stats.drives?.total || 0} color="#059669" />
              <StatCard icon={Ticket} label="Tickets" value={stats.tickets?.total || 0} sub={`${stats.tickets?.open || 0} open`} color="#DC2626" />
              <StatCard icon={UserCog} label="Total Users" value={stats.users?.total || 0} color="#0EA5E9" />
            </div>
          )}

          {/* Donations Tab */}
          {activeTab === "donations" && <DonationsTab donations={donations} onStatusChange={handleStatusChange} />}

          {/* Queries Tab */}
          {activeTab === "queries" && <QueriesTab queries={queries} onStatusChange={handleStatusChange} />}

          {/* Messages Tab */}
          {activeTab === "messages" && (
            <div data-testid="admin-messages-list">
              {activeAdminThread ? (
                <div>
                  <button onClick={() => setActiveAdminThread(null)} className="flex items-center gap-2 text-sm text-[#1E56A0] hover:text-[#174A8A] mb-4 transition-colors" data-testid="admin-thread-back"><Eye className="w-4 h-4" /> Back to all threads</button>
                  <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 mb-4">
                    <p className="text-sm font-medium text-[#0D2847]">{activeAdminThread.senderName} &harr; {activeAdminThread.recipientName}</p>
                    <p className="text-xs text-slate-400">{activeAdminThread.email1} &middot; {activeAdminThread.email2}</p>
                  </div>
                  <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                    {adminThreadMsgs.map((m) => (
                      <div key={m.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`admin-msg-${m.id}`}>
                        <div className="flex items-center justify-between mb-2"><p className="text-xs font-medium text-[#1E56A0]">{m.sender_name || m.sender_email}</p><p className="text-[10px] text-slate-400">{new Date(m.created_at).toLocaleString("en-IN")}</p></div>
                        <p className="text-sm text-[#0D2847] whitespace-pre-wrap break-words">{m.message}</p>
                        <p className="text-[10px] text-slate-400 mt-1">To: {m.recipient_name || m.recipient_email}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {messageThreads.length === 0 ? <p className="text-center text-slate-400 py-12">No message threads yet.</p> :
                    messageThreads.map((t, idx) => (
                      <div key={idx} onClick={() => loadAdminThread(t.sender_email, t.recipient_email, t.sender, t.recipient)}
                        className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 flex items-center justify-between cursor-pointer hover:shadow-md transition-shadow" data-testid={`admin-thread-${idx}`}>
                        <div className="flex items-center gap-4 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0"><MessageCircle className="w-4 h-4 text-[#28A9E2]" /></div>
                          <div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{t.sender} &harr; {t.recipient}</p><p className="text-xs text-slate-400 truncate">{t.last_message?.slice(0, 60) || "..."}</p></div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-[10px] text-slate-400">{new Date(t.last_time).toLocaleDateString("en-IN")}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#28A9E2] text-white">{t.count}</span>
                        </div>
                      </div>
                    ))
                  }
                </div>
              )}
            </div>
          )}

          {/* Tickets Tab */}
          {activeTab === "tickets" && (
            <div className="space-y-3" data-testid="admin-tickets-list">
              {tickets.length === 0 ? <p className="text-center text-slate-400 py-12">No tickets yet.</p> :
                tickets.map((tk) => (
                  <div key={tk.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`admin-ticket-${tk.id}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div><p className="text-sm font-medium text-[#0D2847]">{tk.subject}</p><p className="text-xs text-slate-400">{tk.user_name} ({tk.user_email}) &middot; {new Date(tk.created_at).toLocaleDateString("en-IN")}</p></div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${tk.priority === "high" ? "bg-red-50 text-red-700 border-red-200" : tk.priority === "medium" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}>{tk.priority}</span>
                        <Select value={tk.status} onValueChange={(val) => handleTicketStatusChange(tk.id, val)}>
                          <SelectTrigger className="h-6 text-[10px] w-28 rounded-lg"><SelectValue /></SelectTrigger>
                          <SelectContent><SelectItem value="open">Open</SelectItem><SelectItem value="in-progress">In Progress</SelectItem><SelectItem value="responded">Responded</SelectItem><SelectItem value="resolved">Resolved</SelectItem><SelectItem value="closed">Closed</SelectItem></SelectContent>
                        </Select>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 mb-2 whitespace-pre-wrap">{tk.description}</p>
                    {tk.admin_response && <div className="bg-sky-50 border border-sky-200 rounded-lg p-2 mb-2"><p className="text-[10px] font-medium text-[#1E56A0]">Admin Response:</p><p className="text-xs text-[#0D2847]">{tk.admin_response}</p></div>}
                    <button onClick={() => { const resp = window.prompt("Enter your response:"); handleTicketRespond(tk.id, resp); }} className="text-xs text-[#1E56A0] hover:underline" data-testid={`respond-ticket-${tk.id}`}>{tk.admin_response ? "Update Response" : "Respond"}</button>
                  </div>
                ))
              }
            </div>
          )}

          {/* Role Requests Tab */}
          {activeTab === "role-requests" && (
            <div className="space-y-3" data-testid="admin-role-requests">
              {roleRequests.length === 0 ? <p className="text-center text-slate-400 py-12">No role change requests.</p> :
                roleRequests.map(r => (
                  <div key={r.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`role-req-${r.id}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-[#0D2847]">{r.name} <span className="text-xs text-slate-400">({r.email})</span></p>
                        <p className="text-xs text-slate-500 mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${ROLE_COLORS[r.current_role] || ""}`}>{r.current_role}</span>
                          <span className="mx-2">&rarr;</span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${ROLE_COLORS[r.requested_role] || ""}`}>{r.requested_role}</span>
                        </p>
                        {r.reason && <p className="text-xs text-slate-400 mt-1 italic">"{r.reason}"</p>}
                        <p className="text-[10px] text-slate-400 mt-1">{new Date(r.created_at).toLocaleString("en-IN")}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {r.status === "pending" ? (
                          <>
                            <Button size="sm" onClick={() => handleRoleRequestAction(r.id, "approve")} className="bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg h-8" data-testid={`approve-req-${r.id}`}><CheckCircle className="w-3 h-3 mr-1" /> Approve</Button>
                            <Button size="sm" variant="outline" onClick={() => handleRoleRequestAction(r.id, "reject")} className="text-red-600 border-red-200 hover:bg-red-50 text-xs rounded-lg h-8" data-testid={`reject-req-${r.id}`}><XCircle className="w-3 h-3 mr-1" /> Reject</Button>
                          </>
                        ) : (
                          <StatusBadge status={r.status} />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {/* Drives Tab */}
          {activeTab === "drives" && (
            <div data-testid="admin-drives">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Drives</h2>
                <Button size="sm" onClick={() => setShowDriveForm(!showDriveForm)} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-lg gap-1" data-testid="add-drive-btn"><Plus className="w-4 h-4" /> New Drive</Button>
              </div>
              {showDriveForm && (
                <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 mb-4 space-y-3" data-testid="drive-form">
                  <div className="grid grid-cols-2 gap-3">
                    <Input placeholder="Title" value={driveForm.title} onChange={e => setDriveForm({ ...driveForm, title: e.target.value })} className="rounded-xl" data-testid="drive-title" />
                    <Input placeholder="Location" value={driveForm.location} onChange={e => setDriveForm({ ...driveForm, location: e.target.value })} className="rounded-xl" data-testid="drive-location" />
                  </div>
                  <Input placeholder="Description" value={driveForm.description} onChange={e => setDriveForm({ ...driveForm, description: e.target.value })} className="rounded-xl" data-testid="drive-description" />
                  <div className="grid grid-cols-2 gap-3">
                    <Input type="date" value={driveForm.date} onChange={e => setDriveForm({ ...driveForm, date: e.target.value })} className="rounded-xl" data-testid="drive-date" />
                    <Select value={driveForm.drive_type} onValueChange={val => setDriveForm({ ...driveForm, drive_type: val })}>
                      <SelectTrigger className="rounded-xl" data-testid="drive-type"><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="upcoming">Upcoming</SelectItem><SelectItem value="past">Past</SelectItem></SelectContent>
                    </Select>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateDrive} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="save-drive-btn">Save Drive</Button>
                    <Button variant="outline" onClick={() => setShowDriveForm(false)} className="rounded-xl">Cancel</Button>
                  </div>
                </div>
              )}
              {drives.length === 0 ? <p className="text-center text-slate-400 py-12">No drives yet. Create one!</p> : (
                <div className="space-y-3">
                  {["upcoming", "past"].map(type => {
                    const filtered = drives.filter(d => d.drive_type === type);
                    if (!filtered.length) return null;
                    return (
                      <div key={type}>
                        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">{type === "upcoming" ? "Upcoming Drives" : "Past Drives"}</h3>
                        {filtered.map(d => (
                          <div key={d.id} className={`bg-white rounded-xl border shadow-sm p-4 mb-2 ${type === "upcoming" ? "border-green-100" : "border-slate-100"}`} data-testid={`drive-${d.id}`}>
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="text-sm font-semibold text-[#0D2847]">{d.title}</p>
                                <p className="text-xs text-slate-500 mt-1">{d.description}</p>
                                <div className="flex gap-4 mt-2 text-xs text-slate-400">
                                  <span>{new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
                                  <span>{d.location}</span>
                                </div>
                              </div>
                              <Button variant="ghost" size="sm" onClick={() => handleDeleteDrive(d.id)} className="text-red-500 hover:text-red-700 hover:bg-red-50" data-testid={`delete-drive-${d.id}`}><Trash2 className="w-4 h-4" /></Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Unified Roster Tab */}
          {activeTab === "roster" && (
            <div data-testid="admin-users-list">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-xs text-slate-500">Filter by role:</span>
                {["all", "admin", "volunteer", "member"].map(r => (
                  <button key={r} onClick={() => setRoleFilter(r)}
                    className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${roleFilter === r ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-slate-500 border-sky-100 hover:bg-sky-50"}`}
                    data-testid={`filter-${r}`}>
                    {r === "all" ? `All (${users.length})` : `${r.charAt(0).toUpperCase() + r.slice(1)} (${users.filter(u => u.role === r).length})`}
                  </button>
                ))}
              </div>
              <div className="space-y-3">
                {filteredUsers.length === 0 ? <p className="text-center text-slate-400 py-12">No users found.</p> :
                  filteredUsers.map(u => (
                    <UserAdminCard key={u.email} u={u}
                      onDelete={handleDeleteUser} onUpdate={handleAdminUpdateUser}
                      onAddBadge={handleAddBadge} onRemoveBadge={handleRemoveBadge}
                      isOnWall={wallOfFame.some(w => w.email === u.email)} onToggleWall={handleToggleWallOfFame}
                    />
                  ))
                }
              </div>
            </div>
          )}

          {/* Activity Log Tab */}
          {activeTab === "activity" && (
            <div data-testid="admin-activity-log">
              <div className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden">
                <div className="max-h-[70vh] overflow-y-auto">
                  {activityLogs.length === 0 ? <p className="text-center text-slate-400 py-12">No activity logged yet.</p> :
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-sky-50 border-b border-sky-100">
                        <tr><th className="text-left p-3 text-slate-500 font-medium">Timestamp</th><th className="text-left p-3 text-slate-500 font-medium">Action</th><th className="text-left p-3 text-slate-500 font-medium">User</th><th className="text-left p-3 text-slate-500 font-medium">Details</th></tr>
                      </thead>
                      <tbody>
                        {activityLogs.map((log, i) => (
                          <tr key={log.id || i} className="border-b border-sky-50 hover:bg-sky-50/30">
                            <td className="p-3 text-slate-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</td>
                            <td className="p-3"><span className="px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100 font-medium">{log.action}</span></td>
                            <td className="p-3 text-slate-600">{log.user_email || "—"}</td>
                            <td className="p-3 text-slate-500 max-w-xs truncate">{log.details}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  }
                </div>
              </div>
            </div>
          )}

        </motion.div>
      </div>
    </div>
  );
}

function UserAdminCard({ u, onDelete, onUpdate, onAddBadge, onRemoveBadge, isOnWall, onToggleWall }) {
  const [expanded, setExpanded] = useState(false);
  const [hours, setHours] = useState(u.volunteer_hours || 0);
  const [comments, setComments] = useState(u.admin_comments || "");
  const [suspendReason, setSuspendReason] = useState("");
  const [suspendUntil, setSuspendUntil] = useState("");
  const [newBadge, setNewBadge] = useState("");

  const AVAILABLE_BADGES = ["Star Volunteer of the Month", "Star Volunteer of the Quarter", "Star Volunteer of the Year", "Top Donor", "Rising Star", "Community Builder"];

  return (
    <div className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden" data-testid={`admin-user-${u.email}`}>
      <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30 transition-colors" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3 min-w-0">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${u.status === "suspended" ? "bg-red-100" : "bg-[#1E56A0]/10"}`}>
            <UserCog className={`w-4 h-4 ${u.status === "suspended" ? "text-red-500" : "text-[#1E56A0]"}`} />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-[#0D2847] truncate">
              {u.name}
              {u.status === "suspended" && <span className="text-xs text-red-500 ml-1">[SUSPENDED]</span>}
            </p>
            <p className="text-xs text-slate-400">{u.email} {u.phone ? `| ${u.phone}` : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">{u.volunteer_hours || 0}h</span>
          <span className="text-xs text-[#FF7F00] font-medium">{"\u20B9"}{(u.total_donated || 0).toLocaleString("en-IN")}</span>
          {u.merchandise_issued && <Package className="w-3 h-3 text-green-500" />}
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${ROLE_COLORS[u.role] || ROLE_COLORS.member}`}>{u.role}</span>
          <Eye className="w-4 h-4 text-slate-300" />
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {u.pan_number && <div><span className="text-slate-400">PAN:</span> <span className="text-slate-700">{u.pan_number}</span></div>}
            {u.aadhaar_number && <div><span className="text-slate-400">Aadhaar:</span> <span className="text-slate-700">{u.aadhaar_number}</span></div>}
            {u.address && <div className="col-span-2"><span className="text-slate-400">Address:</span> <span className="text-slate-700">{u.address}</span></div>}
            <div><span className="text-slate-400">Joined:</span> <span className="text-slate-700">{new Date(u.created_at).toLocaleDateString("en-IN")}</span></div>
          </div>

          {/* Badges (only for volunteers) */}
          {u.role === "volunteer" && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-2 flex items-center gap-1"><Award className="w-3 h-3" /> Badges</p>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {(u.badges || []).map(b => (
                  <span key={b} className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100">
                    {b}<button onClick={() => onRemoveBadge(u.email, b)} className="text-red-400 hover:text-red-600 ml-0.5">&times;</button>
                  </span>
                ))}
              </div>
              <div className="flex gap-1.5">
                <select value={newBadge} onChange={e => setNewBadge(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1">
                  <option value="">Add badge...</option>
                  {AVAILABLE_BADGES.filter(b => !(u.badges || []).includes(b)).map(b => <option key={b} value={b}>{b}</option>)}
                </select>
                {newBadge && <button onClick={() => { onAddBadge(u.email, newBadge); setNewBadge(""); }} className="text-xs text-[#1E56A0] hover:underline">Add</button>}
              </div>
            </div>
          )}

          {/* Hours + Merchandise (only for volunteers) */}
          {u.role === "volunteer" && (
            <div className="flex flex-wrap items-end gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Volunteer Hours</label>
                <div className="flex gap-1">
                  <input type="number" value={hours} onChange={e => setHours(parseInt(e.target.value) || 0)} className="w-20 text-xs border border-sky-100 rounded-lg px-2 py-1" data-testid={`hours-input-${u.email}`} />
                  <button onClick={() => onUpdate(u.email, { volunteer_hours: hours })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg hover:bg-[#174A8A]">Save</button>
                </div>
              </div>
              <label className="flex items-center gap-2 text-xs cursor-pointer">
                <input type="checkbox" checked={u.merchandise_issued || false} onChange={e => onUpdate(u.email, { merchandise_issued: e.target.checked })} className="rounded" data-testid={`merch-checkbox-${u.email}`} />
                <Package className="w-3 h-3" /> Merchandise Issued
              </label>
            </div>
          )}

          {/* Admin Comments */}
          <div>
            <label className="text-xs text-slate-400 block mb-1">Admin Comments</label>
            <div className="flex gap-1">
              <textarea value={comments} onChange={e => setComments(e.target.value)} rows={2} className="flex-1 text-xs border border-sky-100 rounded-lg px-2 py-1 resize-none" data-testid={`comments-input-${u.email}`} />
              <button onClick={() => onUpdate(u.email, { admin_comments: comments })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg hover:bg-[#174A8A] self-end">Save</button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-sky-50">
            {/* Role changes */}
            {u.role !== "admin" && (
              <>
                <Select onValueChange={(val) => { if (window.confirm(`Change ${u.name}'s role to ${val}?`)) onUpdate(u.email, { role: val }); }}>
                  <SelectTrigger className="h-8 text-xs w-40 rounded-lg" data-testid={`role-select-${u.email}`}><SelectValue placeholder="Change role..." /></SelectTrigger>
                  <SelectContent>
                    {u.role !== "volunteer" && <SelectItem value="volunteer">Set Volunteer</SelectItem>}
                    {u.role !== "member" && <SelectItem value="member">Set Member</SelectItem>}
                    <SelectItem value="admin">Promote to Admin</SelectItem>
                  </SelectContent>
                </Select>
              </>
            )}
            {u.role === "admin" && (
              <button onClick={() => { if (window.confirm(`Demote ${u.email} from Admin?`)) onUpdate(u.email, { role: "volunteer" }); }}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors" data-testid={`demote-${u.email}`}>
                <Shield className="w-3 h-3" /> Demote
              </button>
            )}
            {u.status !== "suspended" ? (
              <div className="flex items-center gap-1">
                <input placeholder="Reason" value={suspendReason} onChange={e => setSuspendReason(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1 w-28" />
                <input type="date" value={suspendUntil} onChange={e => setSuspendUntil(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1 w-32" />
                <button onClick={() => { if (window.confirm(`Suspend ${u.email}?`)) onUpdate(u.email, { status: "suspended", suspension_reason: suspendReason, suspended_until: suspendUntil }); }}
                  className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors" data-testid={`suspend-${u.email}`}><PauseCircle className="w-3 h-3" /> Suspend</button>
              </div>
            ) : (
              <button onClick={() => onUpdate(u.email, { status: "active" })}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors" data-testid={`unsuspend-${u.email}`}><PlayCircle className="w-3 h-3" /> Unsuspend</button>
            )}
            <button onClick={() => onDelete(u.email)}
              className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors" data-testid={`delete-user-${u.email}`}><Trash2 className="w-3 h-3" /> Remove</button>
            <button onClick={() => onToggleWall(u.email, isOnWall)}
              className={`inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg transition-colors ${isOnWall ? "bg-amber-100 text-amber-800 hover:bg-amber-200 border border-amber-300" : "bg-amber-50 text-amber-600 hover:bg-amber-100"}`}
              data-testid={`wall-toggle-${u.email}`}><Star className={`w-3 h-3 ${isOnWall ? "fill-amber-500" : ""}`} /> {isOnWall ? "On Wall" : "Add to Wall"}</button>
          </div>
        </div>
      )}
    </div>
  );
}
