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
import { LayoutDashboard, IndianRupee, Users, MessageSquare, RefreshCw, CheckCircle, Clock, XCircle, Eye } from "lucide-react";
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
                <div><span className="text-slate-400">Date:</span> <span className="text-slate-600">{new Date(d.created_at).toLocaleDateString("en-IN")}</span></div>
                {d.razorpay_payment_id && <div className="col-span-2"><span className="text-slate-400">Payment ID:</span> <span className="text-slate-600 font-mono text-[10px]">{d.razorpay_payment_id}</span></div>}
              </div>
              {d.message && <p className="text-xs text-slate-500 italic">"{d.message}"</p>}
              <div className="flex items-center gap-2 pt-1">
                <span className="text-xs text-slate-400">Update status:</span>
                <Select value={d.status} onValueChange={(val) => onStatusChange("donations", d.id, val)}>
                  <SelectTrigger className="h-7 text-xs w-32 rounded-lg" data-testid={`donation-status-${d.id}`}><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
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
  const [fetching, setFetching] = useState(true);

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!isAdmin) { setFetching(false); return; }
    setFetching(true);
    try {
      const [statsRes, donRes, volRes, qRes] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/donations"),
        api.get("/admin/volunteers"),
        api.get("/admin/queries"),
      ]);
      setStats(statsRes.data);
      setDonations(donRes.data);
      setVolunteers(volRes.data);
      setQueries(qRes.data);
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="admin-stats">
              <StatCard icon={IndianRupee} label="Total Donations" value={stats.donations.total} sub={`${"\u20B9"}${stats.donations.total_amount.toLocaleString("en-IN")} raised`} color="#FF7F00" />
              <StatCard icon={CheckCircle} label="Confirmed Donations" value={stats.donations.confirmed} sub={`of ${stats.donations.total} total`} color="#16A34A" />
              <StatCard icon={Users} label="Volunteers" value={stats.volunteers.total} sub={`${stats.volunteers.approved} approved`} color="#1E56A0" />
              <StatCard icon={MessageSquare} label="Queries" value={stats.queries.total} sub={`${stats.queries.open} open`} color="#28A9E2" />
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
        </motion.div>
      </div>
    </div>
  );
}
