import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { motion } from "framer-motion";
import { LayoutDashboard, IndianRupee, Users, MessageSquare, RefreshCw, CheckCircle, Clock, XCircle, Eye, Download, Trash2, UserCog, MessageCircle, Ticket, Shield, Award, Package, AlertTriangle, PauseCircle, PlayCircle, Star } from "lucide-react";
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

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500 mb-1">{label}</p>
          <p className="text-3xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{value}</p>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}>
          <Icon className="w-5 h-5" style={{ color }} />
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
              <div className="w-9 h-9 rounded-full bg-[#FF7F00]/10 flex items-center justify-center shrink-0">
                <IndianRupee className="w-4 h-4 text-[#FF7F00]" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-[#0D2847] truncate">{d.name}</p>
                <p className="text-xs text-slate-400">{d.email}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <span className="text-sm font-semibold text-[#0D2847]">{"\u20B9"}{d.amount?.toLocaleString("en-IN")}</span>
              <StatusBadge status={d.status} />
              <Eye className="w-4 h-4 text-slate-300" />
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
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>
                {d.pan_number && (
                  <a href={`${process.env.REACT_APP_BACKEND_URL}/api/donations/${d.id}/certificate`} target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium bg-[#FF7F00]/10 text-[#FF7F00] hover:bg-[#FF7F00]/20 transition-colors"
                    data-testid={`download-cert-${d.id}`}
                  >
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

function VolunteersTab({ volunteers, onStatusChange }) {
  const [expandedId, setExpandedId] = useState(null);

  if (!volunteers.length) return <p className="text-center text-slate-400 py-12">No volunteer registrations yet.</p>;

  return (
    <div className="space-y-3" data-testid="admin-volunteers-list">
      {volunteers.map((v) => (
        <div key={v.id} className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden">
          <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30 transition-colors" onClick={() => setExpandedId(expandedId === v.id ? null : v.id)}>
            <div className="flex items-center gap-4 min-w-0">
              <div className="w-9 h-9 rounded-full bg-[#1E56A0]/10 flex items-center justify-center shrink-0">
                <Users className="w-4 h-4 text-[#1E56A0]" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-[#0D2847] truncate">{v.name}</p>
                <p className="text-xs text-slate-400">{v.city}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <StatusBadge status={v.status} />
              <Eye className="w-4 h-4 text-slate-300" />
            </div>
          </div>
          {expandedId === v.id && (
            <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div><span className="text-slate-400">Email:</span> <span className="text-slate-600">{v.email}</span></div>
                <div><span className="text-slate-400">Phone:</span> <span className="text-slate-600">{v.phone}</span></div>
                <div><span className="text-slate-400">Date:</span> <span className="text-slate-600">{new Date(v.created_at).toLocaleDateString("en-IN")}</span></div>
              </div>
              {v.interests?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {v.interests.map((i) => <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100">{i}</span>)}
                </div>
              )}
              {v.message && <p className="text-xs text-slate-500 italic">"{v.message}"</p>}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-slate-400">Update status:</span>
                <Select value={v.status} onValueChange={(val) => onStatusChange("volunteers", v.id, val)}>
                  <SelectTrigger className="h-7 text-xs w-32 rounded-lg" data-testid={`volunteer-status-${v.id}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="approved">Approved</SelectItem>
                    <SelectItem value="rejected">Rejected</SelectItem>
                  </SelectContent>
                </Select>
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
              <div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0">
                <MessageSquare className="w-4 h-4 text-[#28A9E2]" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-[#0D2847] truncate">{q.subject}</p>
                <p className="text-xs text-slate-400">{q.name} &middot; {q.mission}</p>
              </div>
            </div>
            <div className="flex items-center gap-4 shrink-0">
              <StatusBadge status={q.status} />
              <Eye className="w-4 h-4 text-slate-300" />
            </div>
          </div>
          {expandedId === q.id && (
            <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><span className="text-slate-400">Email:</span> <span className="text-slate-600">{q.email}</span></div>
                <div><span className="text-slate-400">Date:</span> <span className="text-slate-600">{new Date(q.created_at).toLocaleDateString("en-IN")}</span></div>
              </div>
              <p className="text-xs text-slate-600 bg-sky-50/50 rounded-lg p-3">{q.message}</p>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-slate-400">Update status:</span>
                <Select value={q.status} onValueChange={(val) => onStatusChange("queries", q.id, val)}>
                  <SelectTrigger className="h-7 text-xs w-32 rounded-lg" data-testid={`query-status-${q.id}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="responded">Responded</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
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
  const [activeAdminThread, setActiveAdminThread] = useState(null);
  const [adminThreadMsgs, setAdminThreadMsgs] = useState([]);
  const [fetching, setFetching] = useState(true);

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!isAdmin) { setFetching(false); return; }
    setFetching(true);
    try {
      const [statsRes, donRes, volRes, qRes, usersRes, msgsRes, ticketsRes, wofRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/donations"),
        api.get("/admin/volunteers"),
        api.get("/admin/queries"),
        api.get("/admin/users"),
        api.get("/admin/messages"),
        api.get("/admin/tickets"),
        api.get("/wall-of-fame"),
      ]);
      setStats(statsRes.data);
      setDonations(donRes.data);
      setVolunteers(volRes.data);
      setQueries(qRes.data);
      setUsers(usersRes.data);
      setMessageThreads(msgsRes.data);
      setTickets(ticketsRes.data);
      setWallOfFame(wofRes.data);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setFetching(false);
    }
  }, [isAdmin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (collection, itemId, newStatus) => {
    try {
      await api.put(`/admin/${collection}/${itemId}/status`, { status: newStatus });
      toast.success(`Status updated to "${newStatus}"`);
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleDeleteUser = async (email) => {
    if (!window.confirm(`Delete user "${email}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/users/${encodeURIComponent(email)}`);
      toast.success(`User ${email} deleted`);
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const loadAdminThread = async (email1, email2, senderName, recipientName) => {
    try {
      const { data } = await api.get(`/admin/messages/thread/${encodeURIComponent(email1)}/${encodeURIComponent(email2)}`);
      setAdminThreadMsgs(data);
      setActiveAdminThread({ email1, email2, senderName, recipientName });
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleAdminUpdateUser = async (email, updates) => {
    try {
      await api.put(`/admin/users/${encodeURIComponent(email)}/update`, updates);
      toast.success(`User ${email} updated`);
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleAddBadge = async (email, badge) => {
    try {
      await api.post(`/admin/users/${encodeURIComponent(email)}/badge`, { badge });
      toast.success(`Badge "${badge}" added`);
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleRemoveBadge = async (email, badge) => {
    try {
      await api.delete(`/admin/users/${encodeURIComponent(email)}/badge/${encodeURIComponent(badge)}`);
      toast.success(`Badge "${badge}" removed`);
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleTicketStatusChange = async (ticketId, status) => {
    try {
      await api.put(`/admin/tickets/${ticketId}/status`, { status });
      toast.success("Ticket status updated");
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleTicketRespond = async (ticketId, response) => {
    if (!response) return;
    try {
      await api.put(`/admin/tickets/${ticketId}/respond`, { response });
      toast.success("Response sent");
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  const handleToggleWallOfFame = async (email, isOnWall) => {
    try {
      if (isOnWall) {
        await api.delete(`/admin/wall-of-fame/${encodeURIComponent(email)}`);
        toast.success("Removed from Wall of Fame");
      } else {
        await api.post(`/admin/wall-of-fame/${encodeURIComponent(email)}`);
        toast.success("Added to Wall of Fame!");
      }
      fetchData();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-400">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  if (!isAdmin) {
    return (
      <div className="min-h-screen py-12" data-testid="dashboard-page">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center gap-3 mb-8">
              <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 text-[#1E56A0]" />
              </div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">{t.title}</h1>
                <p className="text-sm text-slate-500">{t.welcome}, {user.name || user.email}</p>
              </div>
            </div>
            <div className="bg-white rounded-2xl p-8 sm:p-12 border border-sky-100 shadow-sm text-center" data-testid="dashboard-placeholder">
              <div className="w-20 h-20 rounded-full bg-sky-50 flex items-center justify-center mx-auto mb-6">
                <LayoutDashboard className="w-10 h-10 text-slate-300" />
              </div>
              <p className="text-base text-slate-500 leading-relaxed max-w-md mx-auto">{t.placeholder}</p>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "donations", label: "Donations", icon: IndianRupee, count: donations.length },
    { id: "volunteers", label: "Volunteers", icon: Users, count: volunteers.length },
    { id: "queries", label: "Queries", icon: MessageSquare, count: queries.length },
    { id: "messages", label: "Messages", icon: MessageCircle, count: messageThreads.length },
    { id: "tickets", label: "Tickets", icon: Ticket, count: tickets.length },
    { id: "users", label: "Users", icon: UserCog, count: users.length },
  ];

  return (
    <div className="min-h-screen py-8" data-testid="dashboard-page">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center">
                <LayoutDashboard className="w-6 h-6 text-[#1E56A0]" />
              </div>
              <div>
                <h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">
                  Admin Dashboard
                </h1>
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
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
                  activeTab === id
                    ? "bg-[#1E56A0] text-white shadow-sm"
                    : "text-slate-500 hover:text-[#1E56A0] hover:bg-sky-50"
                }`}
                data-testid={`tab-${id}`}
              >
                <TabIcon className="w-4 h-4" />
                {label}
                {count !== undefined && <span className={`text-xs px-1.5 py-0.5 rounded-full ${activeTab === id ? "bg-white/20" : "bg-sky-100 text-[#1E56A0]"}`}>{count}</span>}
              </button>
            ))}
          </div>

          {/* Overview */}
          {activeTab === "overview" && stats && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4" data-testid="admin-stats">
              <StatCard icon={IndianRupee} label="Total Donations" value={stats.donations.total} sub={`${"\u20B9"}${stats.donations.total_amount.toLocaleString("en-IN")} raised`} color="#FF7F00" />
              <StatCard icon={CheckCircle} label="Confirmed" value={stats.donations.confirmed} sub={`of ${stats.donations.total}`} color="#16A34A" />
              <StatCard icon={Users} label="Volunteers" value={stats.volunteers.total} sub={`${stats.volunteers.approved} approved`} color="#1E56A0" />
              <StatCard icon={MessageSquare} label="Queries" value={stats.queries.total} sub={`${stats.queries.open} open`} color="#28A9E2" />
              <StatCard icon={Ticket} label="Tickets" value={stats.tickets?.total || 0} sub={`${stats.tickets?.open || 0} open`} color="#DC2626" />
              <StatCard icon={UserCog} label="Users" value={stats.users?.total || 0} color="#7C3AED" />
            </div>
          )}

          {activeTab === "overview" && !stats && fetching && (
            <div className="text-center py-16 text-slate-400">Loading stats...</div>
          )}

          {/* Donations Tab */}
          {activeTab === "donations" && <DonationsTab donations={donations} onStatusChange={handleStatusChange} />}

          {/* Volunteers Tab */}
          {activeTab === "volunteers" && <VolunteersTab volunteers={volunteers} onStatusChange={handleStatusChange} />}

          {/* Queries Tab */}
          {activeTab === "queries" && <QueriesTab queries={queries} onStatusChange={handleStatusChange} />}

          {/* Messages Tab */}
          {activeTab === "messages" && (
            <div data-testid="admin-messages-list">
              {activeAdminThread ? (
                <div>
                  <button
                    onClick={() => setActiveAdminThread(null)}
                    className="flex items-center gap-2 text-sm text-[#1E56A0] hover:text-[#174A8A] mb-4 transition-colors"
                    data-testid="admin-thread-back"
                  >
                    <Eye className="w-4 h-4" /> Back to all threads
                  </button>
                  <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 mb-4">
                    <p className="text-sm font-medium text-[#0D2847]">
                      {activeAdminThread.senderName} &harr; {activeAdminThread.recipientName}
                    </p>
                    <p className="text-xs text-slate-400">{activeAdminThread.email1} &middot; {activeAdminThread.email2}</p>
                  </div>
                  <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                    {adminThreadMsgs.map((m) => (
                      <div key={m.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`admin-msg-${m.id}`}>
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-xs font-medium text-[#1E56A0]">{m.sender_name || m.sender_email}</p>
                          <p className="text-[10px] text-slate-400">{new Date(m.created_at).toLocaleString("en-IN")}</p>
                        </div>
                        <p className="text-sm text-[#0D2847] whitespace-pre-wrap break-words">{m.message}</p>
                        <p className="text-[10px] text-slate-400 mt-1">To: {m.recipient_name || m.recipient_email}</p>
                      </div>
                    ))}
                    {adminThreadMsgs.length === 0 && <p className="text-center text-slate-400 py-8">No messages in this thread.</p>}
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {messageThreads.length === 0 ? <p className="text-center text-slate-400 py-12">No message threads yet.</p> :
                    messageThreads.map((t, idx) => (
                      <div
                        key={idx}
                        onClick={() => loadAdminThread(t.sender_email, t.recipient_email, t.sender, t.recipient)}
                        className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 flex items-center justify-between cursor-pointer hover:shadow-md transition-shadow"
                        data-testid={`admin-thread-${idx}`}
                      >
                        <div className="flex items-center gap-4 min-w-0">
                          <div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0">
                            <MessageCircle className="w-4 h-4 text-[#28A9E2]" />
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-[#0D2847] truncate">{t.sender} &harr; {t.recipient}</p>
                            <p className="text-xs text-slate-400 truncate">{t.last_message?.slice(0, 60) || "..."}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-[10px] text-slate-400">{new Date(t.last_time).toLocaleDateString("en-IN")}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#28A9E2] text-white">{t.count}</span>
                          <Eye className="w-4 h-4 text-slate-300" />
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
                      <div>
                        <p className="text-sm font-medium text-[#0D2847]">{tk.subject}</p>
                        <p className="text-xs text-slate-400">{tk.user_name} ({tk.user_email}) &middot; {new Date(tk.created_at).toLocaleDateString("en-IN")}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${tk.priority === "high" ? "bg-red-50 text-red-700 border-red-200" : tk.priority === "medium" ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}>{tk.priority}</span>
                        <Select value={tk.status} onValueChange={(val) => handleTicketStatusChange(tk.id, val)}>
                          <SelectTrigger className="h-6 text-[10px] w-28 rounded-lg"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="open">Open</SelectItem>
                            <SelectItem value="in-progress">In Progress</SelectItem>
                            <SelectItem value="responded">Responded</SelectItem>
                            <SelectItem value="resolved">Resolved</SelectItem>
                            <SelectItem value="closed">Closed</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <p className="text-xs text-slate-600 mb-2 whitespace-pre-wrap">{tk.description}</p>
                    {tk.admin_response && (
                      <div className="bg-sky-50 border border-sky-200 rounded-lg p-2 mb-2">
                        <p className="text-[10px] font-medium text-[#1E56A0]">Admin Response:</p>
                        <p className="text-xs text-[#0D2847]">{tk.admin_response}</p>
                      </div>
                    )}
                    <button onClick={() => { const resp = window.prompt("Enter your response:"); handleTicketRespond(tk.id, resp); }}
                      className="text-xs text-[#1E56A0] hover:underline" data-testid={`respond-ticket-${tk.id}`}>
                      {tk.admin_response ? "Update Response" : "Respond"}
                    </button>
                  </div>
                ))
              }
            </div>
          )}

          {/* Users Tab - Enhanced */}
          {activeTab === "users" && (
            <div className="space-y-3" data-testid="admin-users-list">
              {users.length === 0 ? <p className="text-center text-slate-400 py-12">No users yet.</p> :
                users.map((u) => (
                  <UserAdminCard key={u.email} u={u}
                    onDelete={handleDeleteUser}
                    onUpdate={handleAdminUpdateUser}
                    onAddBadge={handleAddBadge}
                    onRemoveBadge={handleRemoveBadge}
                    isOnWall={wallOfFame.some((w) => w.email === u.email)}
                    onToggleWall={handleToggleWallOfFame}
                  />
                ))
              }
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
              {u.name} <span className="text-xs text-slate-400 ml-1">({u.role})</span>
              {u.status === "suspended" && <span className="text-xs text-red-500 ml-1">[SUSPENDED]</span>}
            </p>
            <p className="text-xs text-slate-400">{u.email} {u.phone ? `| ${u.phone}` : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">{u.volunteer_hours || 0}h</span>
          <span className="text-xs text-[#FF7F00] font-medium">{"\u20B9"}{(u.total_donated || 0).toLocaleString("en-IN")}</span>
          {u.merchandise_issued && <Package className="w-3 h-3 text-green-500" />}
          <span className={`text-xs px-2 py-0.5 rounded-full border ${u.role === "admin" ? "bg-blue-50 text-blue-700 border-blue-200" : "bg-slate-50 text-slate-600 border-slate-200"}`}>{u.role}</span>
          <Eye className="w-4 h-4 text-slate-300" />
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-4">
          {/* Identity */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            {u.pan_number && <div><span className="text-slate-400">PAN:</span> <span className="text-slate-700">{u.pan_number}</span></div>}
            {u.aadhaar_number && <div><span className="text-slate-400">Aadhaar:</span> <span className="text-slate-700">{u.aadhaar_number}</span></div>}
            {u.address && <div className="col-span-2"><span className="text-slate-400">Address:</span> <span className="text-slate-700">{u.address}</span></div>}
            <div><span className="text-slate-400">Joined:</span> <span className="text-slate-700">{new Date(u.created_at).toLocaleDateString("en-IN")}</span></div>
          </div>

          {/* Badges */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2 flex items-center gap-1"><Award className="w-3 h-3" /> Badges</p>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {(u.badges || []).map((b) => (
                <span key={b} className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100">
                  {b}
                  <button onClick={() => onRemoveBadge(u.email, b)} className="text-red-400 hover:text-red-600 ml-0.5">&times;</button>
                </span>
              ))}
            </div>
            <div className="flex gap-1.5">
              <select value={newBadge} onChange={(e) => setNewBadge(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1">
                <option value="">Add badge...</option>
                {AVAILABLE_BADGES.filter((b) => !(u.badges || []).includes(b)).map((b) => <option key={b} value={b}>{b}</option>)}
              </select>
              {newBadge && <button onClick={() => { onAddBadge(u.email, newBadge); setNewBadge(""); }} className="text-xs text-[#1E56A0] hover:underline">Add</button>}
            </div>
          </div>

          {/* Hours + Merchandise */}
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Volunteer Hours</label>
              <div className="flex gap-1">
                <input type="number" value={hours} onChange={(e) => setHours(parseInt(e.target.value) || 0)} className="w-20 text-xs border border-sky-100 rounded-lg px-2 py-1" data-testid={`hours-input-${u.email}`} />
                <button onClick={() => onUpdate(u.email, { volunteer_hours: hours })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg hover:bg-[#174A8A]">Save</button>
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs cursor-pointer">
              <input type="checkbox" checked={u.merchandise_issued || false} onChange={(e) => onUpdate(u.email, { merchandise_issued: e.target.checked })} className="rounded" data-testid={`merch-checkbox-${u.email}`} />
              <Package className="w-3 h-3" /> Merchandise Issued
            </label>
          </div>

          {/* Admin Comments */}
          <div>
            <label className="text-xs text-slate-400 block mb-1">Admin Comments</label>
            <div className="flex gap-1">
              <textarea value={comments} onChange={(e) => setComments(e.target.value)} rows={2} className="flex-1 text-xs border border-sky-100 rounded-lg px-2 py-1 resize-none" data-testid={`comments-input-${u.email}`} />
              <button onClick={() => onUpdate(u.email, { admin_comments: comments })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg hover:bg-[#174A8A] self-end">Save</button>
            </div>
          </div>

          {/* Actions: Promote / Suspend / Delete */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-sky-50">
            {u.role !== "admin" ? (
              <button onClick={() => { if (window.confirm(`Promote ${u.email} to Admin?`)) onUpdate(u.email, { role: "admin" }); }}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors" data-testid={`promote-${u.email}`}>
                <Shield className="w-3 h-3" /> Promote to Admin
              </button>
            ) : (
              <button onClick={() => { if (window.confirm(`Demote ${u.email} to Volunteer?`)) onUpdate(u.email, { role: "volunteer" }); }}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors" data-testid={`demote-${u.email}`}>
                <Shield className="w-3 h-3" /> Demote to Volunteer
              </button>
            )}
            {u.status !== "suspended" ? (
              <div className="flex items-center gap-1">
                <input placeholder="Reason" value={suspendReason} onChange={(e) => setSuspendReason(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1 w-28" />
                <input type="date" value={suspendUntil} onChange={(e) => setSuspendUntil(e.target.value)} className="text-xs border border-sky-100 rounded-lg px-2 py-1 w-32" />
                <button onClick={() => { if (window.confirm(`Suspend ${u.email}?`)) onUpdate(u.email, { status: "suspended", suspension_reason: suspendReason, suspended_until: suspendUntil }); }}
                  className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100 transition-colors" data-testid={`suspend-${u.email}`}>
                  <PauseCircle className="w-3 h-3" /> Suspend
                </button>
              </div>
            ) : (
              <button onClick={() => onUpdate(u.email, { status: "active" })}
                className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors" data-testid={`unsuspend-${u.email}`}>
                <PlayCircle className="w-3 h-3" /> Unsuspend
              </button>
            )}
            <button onClick={() => onDelete(u.email)}
              className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors" data-testid={`delete-user-${u.email}`}>
              <Trash2 className="w-3 h-3" /> Delete
            </button>
            <button onClick={() => onToggleWall(u.email, isOnWall)}
              className={`inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg transition-colors ${isOnWall ? "bg-amber-100 text-amber-800 hover:bg-amber-200 border border-amber-300" : "bg-amber-50 text-amber-600 hover:bg-amber-100"}`}
              data-testid={`wall-toggle-${u.email}`}>
              <Star className={`w-3 h-3 ${isOnWall ? "fill-amber-500" : ""}`} /> {isOnWall ? "On Wall of Fame" : "Add to Wall of Fame"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
