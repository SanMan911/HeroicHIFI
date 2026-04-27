import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import api, { formatApiError } from "../lib/api";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Input } from "../components/ui/input";
import { motion } from "framer-motion";
import { LayoutDashboard, IndianRupee, Users, MessageSquare, RefreshCw, CheckCircle, Clock, XCircle, Eye, Download, Trash2, UserCog, MessageCircle, Ticket, Shield, Award, Package, PauseCircle, PlayCircle, Star, ArrowUpDown, CalendarDays, Activity, Plus, Mail, Bell, FileText, ChevronDown, ChevronUp, Crown, Repeat } from "lucide-react";
import { toast } from "sonner";

const STATUS_COLORS = { pending: "bg-amber-100 text-amber-800 border-amber-200", confirmed: "bg-green-100 text-green-800 border-green-200", approved: "bg-green-100 text-green-800 border-green-200", rejected: "bg-red-100 text-red-800 border-red-200", failed: "bg-red-100 text-red-800 border-red-200", open: "bg-blue-100 text-blue-800 border-blue-200", responded: "bg-cyan-100 text-cyan-800 border-cyan-200", closed: "bg-slate-100 text-slate-600 border-slate-200" };
const ROLE_COLORS = { admin: "bg-blue-50 text-blue-700 border-blue-200", volunteer: "bg-green-50 text-green-700 border-green-200", member: "bg-slate-50 text-slate-600 border-slate-200" };
const MISSIONS = [
  { slug: "mission-shakti", name: "Mission Shakti" }, { slug: "mission-swabhiman", name: "Mission Swabhiman" },
  { slug: "mission-roshni", name: "Mission Roshni" }, { slug: "mission-koi-bhookha-na-soye", name: "Mission Koi Bhookha Na Soye" },
  { slug: "mission-paryavaran", name: "Mission Paryavaran" }, { slug: "mission-karuna", name: "Mission Karuna" },
  { slug: "mission-paridhan", name: "Mission Paridhan" },
];

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (<div className="bg-white rounded-2xl p-5 border border-sky-100 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-xs text-slate-500 mb-1">{label}</p><p className="text-2xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{value}</p>{sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}</div><div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${color}15` }}><Icon className="w-4 h-4" style={{ color }} /></div></div></div>);
}
function StatusBadge({ status }) {
  return (<span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[status] || STATUS_COLORS.pending}`}>{status}</span>);
}

// ── Event Report Modal (mandatory after event) ──
function EventReportModal({ drive, volunteers, onSubmit, onClose }) {
  const [form, setForm] = useState({ time_spent: "", resources_spent: "", summary: "", issues: "", outcome: "", admin_rating: 5, attendance: [] });
  const toggleAttendance = (email) => {
    setForm(f => ({ ...f, attendance: f.attendance.includes(email) ? f.attendance.filter(e => e !== email) : [...f.attendance, email] }));
  };
  const [submitting, setSubmitting] = useState(false);
  const handleSubmit = async () => {
    if (!form.time_spent || !form.summary || !form.outcome) { toast.error("Please fill time spent, summary, and outcome"); return; }
    setSubmitting(true);
    try { await onSubmit({ ...form, drive_id: drive.id }); } finally { setSubmitting(false); }
  };
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" data-testid="event-report-modal">
      <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-sky-100">
          <h2 className="text-xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Event Report Required</h2>
          <p className="text-sm text-slate-500 mt-1">"{drive.title}" on {new Date(drive.date).toLocaleDateString("en-IN")} at {drive.location}</p>
          <p className="text-xs text-red-500 mt-2">This report is mandatory. Please fill all details.</p>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-500 block mb-1">Time Spent *</label><Input value={form.time_spent} onChange={e => setForm({...form, time_spent: e.target.value})} placeholder="e.g., 4 hours" className="rounded-xl" data-testid="report-time" /></div>
            <div><label className="text-xs text-slate-500 block mb-1">Admin Rating (1-10) *</label><Input type="number" min={1} max={10} value={form.admin_rating} onChange={e => setForm({...form, admin_rating: parseInt(e.target.value) || 5})} className="rounded-xl" data-testid="report-rating" /></div>
          </div>
          <div><label className="text-xs text-slate-500 block mb-1">Resources Spent *</label><Input value={form.resources_spent} onChange={e => setForm({...form, resources_spent: e.target.value})} placeholder="e.g., 50 saplings, refreshments" className="rounded-xl" data-testid="report-resources" /></div>
          <div><label className="text-xs text-slate-500 block mb-1">Event Summary *</label><textarea value={form.summary} onChange={e => setForm({...form, summary: e.target.value})} rows={3} className="w-full text-sm border border-sky-100 rounded-xl px-3 py-2 resize-none" placeholder="Brief about the event..." data-testid="report-summary" /></div>
          <div><label className="text-xs text-slate-500 block mb-1">Outcome *</label><textarea value={form.outcome} onChange={e => setForm({...form, outcome: e.target.value})} rows={2} className="w-full text-sm border border-sky-100 rounded-xl px-3 py-2 resize-none" placeholder="What was achieved..." data-testid="report-outcome" /></div>
          <div><label className="text-xs text-slate-500 block mb-1">Issues Faced</label><textarea value={form.issues} onChange={e => setForm({...form, issues: e.target.value})} rows={2} className="w-full text-sm border border-sky-100 rounded-xl px-3 py-2 resize-none" placeholder="Any problems encountered..." data-testid="report-issues" /></div>
          <div>
            <label className="text-xs text-slate-500 block mb-2">Volunteer Attendance (check who participated)</label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border border-sky-100 rounded-xl p-3" data-testid="report-attendance">
              {volunteers.filter(v => v.role === "volunteer").map(v => (
                <label key={v.email} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-sky-50 rounded-lg p-1">
                  <input type="checkbox" checked={form.attendance.includes(v.email)} onChange={() => toggleAttendance(v.email)} className="rounded" data-testid={`attend-${v.email}`} />
                  <span className="text-slate-700">{v.name}</span><span className="text-[10px] text-slate-400">{v.email}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="p-6 border-t border-sky-100 flex justify-end gap-3">
          <Button onClick={handleSubmit} disabled={submitting} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="submit-report-btn">
            {submitting ? "Generating Article..." : "Submit Report & Generate Article"}
          </Button>
        </div>
      </motion.div>
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
  const [specFilter, setSpecFilter] = useState("all");
  const [myRoleRequests, setMyRoleRequests] = useState([]);
  const [roleRequestForm, setRoleRequestForm] = useState({ requested_role: "", reason: "" });
  const [pendingEvents, setPendingEvents] = useState([]);
  const [showEventReport, setShowEventReport] = useState(null);
  const [emailBlasts, setEmailBlasts] = useState([]);
  const [promotionRequests, setPromotionRequests] = useState([]);
  const [eventReports, setEventReports] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [webhookHealth, setWebhookHealth] = useState(null);

  const isAdmin = user?.role === "admin";

  const fetchData = useCallback(async () => {
    if (!isAdmin) {
      try {
        const [reqRes, drivesRes, notifRes] = await Promise.all([
          api.get("/role-requests/mine"), api.get("/drives"), api.get("/notifications"),
        ]);
        setMyRoleRequests(reqRes.data); setDrives(drivesRes.data); setNotifications(notifRes.data);
      } catch {}
      setFetching(false);
      return;
    }
    setFetching(true);
    try {
      const [statsRes, donRes, volRes, qRes, usersRes, msgsRes, ticketsRes, wofRes, rrRes, drivesRes, logsRes, pendingRes, blastsRes, promoRes, reportsRes, notifRes, subsRes, hookRes] = await Promise.all([
        api.get("/admin/stats"), api.get("/admin/donations"), api.get("/admin/volunteers"),
        api.get("/admin/queries"), api.get("/admin/users"), api.get("/admin/messages"),
        api.get("/admin/tickets"), api.get("/wall-of-fame"), api.get("/admin/role-requests"),
        api.get("/drives"), api.get("/admin/activity-logs?limit=200"),
        api.get("/admin/events/pending"), api.get("/admin/email-blasts"),
        api.get("/admin/promote-requests"), api.get("/admin/events/reports"), api.get("/notifications"),
        api.get("/admin/subscriptions"),
        api.get("/admin/webhook-health?limit=15"),
      ]);
      setStats(statsRes.data); setDonations(donRes.data); setVolunteers(volRes.data);
      setQueries(qRes.data); setUsers(usersRes.data); setMessageThreads(msgsRes.data);
      setTickets(ticketsRes.data); setWallOfFame(wofRes.data); setRoleRequests(rrRes.data);
      setDrives(drivesRes.data); setActivityLogs(logsRes.data); setPendingEvents(pendingRes.data);
      setEmailBlasts(blastsRes.data); setPromotionRequests(promoRes.data);
      setEventReports(reportsRes.data); setNotifications(notifRes.data);
      setSubscriptions(subsRes.data);
      setWebhookHealth(hookRes.data);
      // Show mandatory event report modal
      if (pendingRes.data.length > 0) {
        setShowEventReport(pendingRes.data[0]);
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setFetching(false); }
  }, [isAdmin]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleStatusChange = async (collection, itemId, newStatus) => { try { await api.put(`/admin/${collection}/${itemId}/status`, { status: newStatus }); toast.success(`Status updated`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleDeleteUser = async (email, reason) => { try { await api.delete(`/admin/users/${encodeURIComponent(email)}`, { data: { reason } }); toast.success(`User removed`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleVerifyPan = async (email) => { try { const { data } = await api.post(`/admin/users/${encodeURIComponent(email)}/verify-pan`); toast.success(`PAN check (${data.mode}): ${data.status}`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const loadAdminThread = async (email1, email2, senderName, recipientName) => { try { const { data } = await api.get(`/admin/messages/thread/${encodeURIComponent(email1)}/${encodeURIComponent(email2)}`); setAdminThreadMsgs(data); setActiveAdminThread({ email1, email2, senderName, recipientName }); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleAdminUpdateUser = async (email, updates) => { try { await api.put(`/admin/users/${encodeURIComponent(email)}/update`, updates); toast.success(`Updated`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleAddBadge = async (email, badge) => { try { await api.post(`/admin/users/${encodeURIComponent(email)}/badge`, { badge }); toast.success(`Badge added`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleRemoveBadge = async (email, badge) => { try { await api.delete(`/admin/users/${encodeURIComponent(email)}/badge/${encodeURIComponent(badge)}`); toast.success(`Badge removed`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleTicketStatusChange = async (id, status) => { try { await api.put(`/admin/tickets/${id}/status`, { status }); toast.success("Updated"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleTicketRespond = async (id, response) => { if (!response) return; try { await api.put(`/admin/tickets/${id}/respond`, { response }); toast.success("Sent"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleToggleWallOfFame = async (email, isOnWall) => { try { if (isOnWall) { await api.delete(`/admin/wall-of-fame/${encodeURIComponent(email)}`); } else { await api.post(`/admin/wall-of-fame/${encodeURIComponent(email)}`); } toast.success(isOnWall ? "Removed" : "Added"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleRoleRequestAction = async (id, action) => { try { await api.put(`/admin/role-requests/${id}/${action}`); toast.success(`${action}d`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleSubmitRoleRequest = async () => { if (!roleRequestForm.requested_role) return; try { await api.post("/role-requests", roleRequestForm); toast.success("Submitted!"); setRoleRequestForm({ requested_role: "", reason: "" }); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail, err)); } };
  const handlePromotionAction = async (id, action) => { try { await api.put(`/admin/promote-requests/${id}/${action}`); toast.success(`${action}d`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleEventReportSubmit = async (data) => {
    try { await api.post("/admin/events/report", data); toast.success("Report submitted & article generated!"); setShowEventReport(null); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  // Drive form state
  const [driveForm, setDriveForm] = useState({ title: "", description: "", date: "", location: "", drive_type: "upcoming", mission_slug: "", estimated_days: 1, time: "" });
  const [showDriveForm, setShowDriveForm] = useState(false);
  const handleCreateDrive = async () => { if (!driveForm.title || !driveForm.date || !driveForm.location) { toast.error("Fill title, date, location"); return; } try { await api.post("/admin/drives", driveForm); toast.success("Created!"); setDriveForm({ title: "", description: "", date: "", location: "", drive_type: "upcoming", mission_slug: "", estimated_days: 1, time: "" }); setShowDriveForm(false); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleDeleteDrive = async (id) => { if (!window.confirm("Delete?")) return; try { await api.delete(`/admin/drives/${id}`); toast.success("Deleted"); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };

  // Email blast form
  const [blastForm, setBlastForm] = useState({ subject: "", body: "", target: "all" });
  const [blastSending, setBlastSending] = useState(false);
  const handleSendBlast = async () => { if (!blastForm.subject || !blastForm.body) { toast.error("Fill subject and body"); return; } setBlastSending(true); try { const { data } = await api.post("/admin/email-blast", blastForm); toast.success(data.message); setBlastForm({ subject: "", body: "", target: "all" }); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } finally { setBlastSending(false); } };

  // Promote form
  const [promoteEmail, setPromoteEmail] = useState("");
  const [promoteReason, setPromoteReason] = useState("");
  const handlePromote = async () => { if (!promoteEmail) return; try { const { data } = await api.post("/admin/promote-request", { target_email: promoteEmail, reason: promoteReason }); toast.success(data.message); setPromoteEmail(""); setPromoteReason(""); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };

  // Heroic Patrons / Subscriptions
  const handleRecomputePatrons = async () => { try { const { data } = await api.post("/admin/patrons/recompute"); toast.success(data.message); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleSimulateCharge = async (subId) => { try { const { data } = await api.post(`/admin/subscriptions/${subId}/simulate-charge`); toast.success(`Charge simulated. ${data.patron?.promoted ? "🎉 Promoted to Heroic Patron!" : `Charges: ${data.patron?.charge_count || 0}/6`}`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };
  const handleReplayWebhook = async (eventId) => { try { const { data } = await api.post(`/admin/webhook-events/${eventId}/replay`); toast.success(`Replayed: ${data.side_effects?.join(", ") || "no side effects"}`); fetchData(); } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); } };

  if (loading) return <div className="min-h-screen flex items-center justify-center text-slate-400">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  // ── Non-Admin Dashboard ──
  if (!isAdmin) {
    const upcomingDrives = drives.filter(d => d.drive_type === "upcoming");
    const pastDrives = drives.filter(d => d.drive_type === "past");
    const unreadNotifs = notifications.filter(n => !n.read);
    return (
      <div className="min-h-screen py-12" data-testid="dashboard-page">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center"><LayoutDashboard className="w-6 h-6 text-[#1E56A0]" /></div>
                <div><h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">{t.title}</h1><p className="text-sm text-slate-500">{t.welcome}, {user.name || user.email} <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ml-2 ${ROLE_COLORS[user.role] || ROLE_COLORS.member}`}>{user.role}</span></p></div>
              </div>
            </div>
            {/* Notifications */}
            {unreadNotifs.length > 0 && (
              <div className="space-y-2" data-testid="user-notifications">
                <h3 className="text-sm font-semibold text-[#0D2847] flex items-center gap-2"><Bell className="w-4 h-4 text-[#FF7F00]" /> Notifications ({unreadNotifs.length})</h3>
                {unreadNotifs.slice(0, 5).map(n => (
                  <div key={n.id} className="bg-[#FF7F00]/5 border border-[#FF7F00]/20 rounded-xl p-3 flex items-start justify-between">
                    <div><p className="text-sm text-[#0D2847] font-medium">{n.title}</p><p className="text-xs text-slate-500">{n.message}</p><p className="text-[10px] text-slate-400 mt-1">{new Date(n.created_at).toLocaleString("en-IN")}</p></div>
                    <button onClick={async () => { await api.put(`/notifications/${n.id}/read`); fetchData(); }} className="text-xs text-[#1E56A0] hover:underline shrink-0">Mark read</button>
                  </div>
                ))}
              </div>
            )}
            {/* Role Change */}
            <div className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm" data-testid="role-change-section">
              <h2 className="text-lg font-semibold text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}><ArrowUpDown className="w-5 h-5 text-[#1E56A0]" /> Request Role Change</h2>
              {myRoleRequests.some(r => r.status === "pending") ? (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">Pending request. Please wait for admin review.</div>
              ) : (
                <div className="flex flex-col sm:flex-row gap-3">
                  <Select value={roleRequestForm.requested_role} onValueChange={val => setRoleRequestForm({...roleRequestForm, requested_role: val})}><SelectTrigger className="w-48 rounded-xl" data-testid="role-request-select"><SelectValue placeholder="Select role..." /></SelectTrigger><SelectContent>{user.role !== "volunteer" && <SelectItem value="volunteer">Volunteer</SelectItem>}{user.role !== "member" && <SelectItem value="member">Member</SelectItem>}</SelectContent></Select>
                  <Input placeholder="Reason (optional)" value={roleRequestForm.reason} onChange={e => setRoleRequestForm({...roleRequestForm, reason: e.target.value})} className="flex-1 rounded-xl" data-testid="role-request-reason" />
                  <Button onClick={handleSubmitRoleRequest} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="role-request-submit">Submit</Button>
                </div>
              )}
            </div>
            {/* Drives */}
            {[{ list: upcomingDrives, label: "Upcoming Drives", color: "green", icon: CalendarDays, testId: "upcoming-drives" }, { list: pastDrives, label: "Past Drives", color: "slate", icon: Clock, testId: "past-drives" }].map(({ list, label, color, icon: DIcon, testId }) => list.length > 0 && (
              <div key={testId} className="bg-white rounded-2xl p-6 border border-sky-100 shadow-sm" data-testid={testId}>
                <h2 className="text-lg font-semibold text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}><DIcon className={`w-5 h-5 text-${color}-600`} /> {label}</h2>
                <div className="space-y-3">{list.map(d => (<div key={d.id} className={`border border-${color}-100 rounded-xl p-4 bg-${color}-50/30`}><p className="text-sm font-semibold text-[#0D2847]">{d.title}</p><p className="text-xs text-slate-500 mt-1">{d.description}</p><div className="flex gap-4 mt-2 text-xs text-slate-400"><span>{new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span><span>{d.location}</span>{d.mission_slug && <span>{d.mission_slug}</span>}</div></div>))}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    );
  }

  // ── ADMIN DASHBOARD ──
  const SPECIALIZATIONS = [
    { key: "education", label: "Education" }, { key: "healthcare", label: "Healthcare" },
    { key: "environment", label: "Environment" }, { key: "food", label: "Food Distribution" },
    { key: "women", label: "Women Empowerment" }, { key: "animal", label: "Animal Welfare" },
    { key: "clothing", label: "Clothing Drives" },
  ];
  const filteredUsers = users.filter(u =>
    (roleFilter === "all" || u.role === roleFilter) &&
    (specFilter === "all" || (u.specializations || []).includes(specFilter))
  );
  const pendingRoleRequests = roleRequests.filter(r => r.status === "pending");
  const pendingPromos = promotionRequests.filter(r => r.status === "pending");
  const admins = users.filter(u => u.role === "admin");

  const tabs = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    { id: "donations", label: "Donations", icon: IndianRupee, count: donations.length },
    { id: "roster", label: "Roster", icon: Users, count: users.length },
    { id: "role-requests", label: "Requests", icon: ArrowUpDown, count: pendingRoleRequests.length },
    { id: "drives", label: "Events", icon: CalendarDays, count: drives.length },
    { id: "email-blast", label: "Email", icon: Mail },
    { id: "queries", label: "Queries", icon: MessageSquare, count: queries.length },
    { id: "messages", label: "Messages", icon: MessageCircle, count: messageThreads.length },
    { id: "tickets", label: "Tickets", icon: Ticket, count: tickets.length },
    { id: "promotions", label: "Admins", icon: Shield, count: pendingPromos.length },
    { id: "patrons", label: "Patrons", icon: Crown, count: subscriptions.filter(s => s.status !== "cancelled").length },
    { id: "articles", label: "Articles", icon: FileText, count: eventReports.length },
    { id: "activity", label: "Log", icon: Activity },
  ];

  return (
    <div className="min-h-screen py-8" data-testid="dashboard-page">
      {/* Mandatory Event Report Modal */}
      {showEventReport && <EventReportModal drive={showEventReport} volunteers={users} onSubmit={handleEventReportSubmit} />}

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-[#1E56A0]/10 flex items-center justify-center"><LayoutDashboard className="w-6 h-6 text-[#1E56A0]" /></div>
              <div><h1 className="text-3xl sm:text-4xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }} data-testid="dashboard-title">Admin Dashboard</h1><p className="text-sm text-slate-500">{t.welcome}, {user.name || user.email}</p></div>
            </div>
            <div className="flex items-center gap-3">
              {notifications.filter(n => !n.read).length > 0 && <span className="relative"><Bell className="w-5 h-5 text-[#FF7F00]" /><span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[10px] flex items-center justify-center">{notifications.filter(n => !n.read).length}</span></span>}
              <Button variant="outline" size="sm" onClick={fetchData} disabled={fetching} className="rounded-full gap-2" data-testid="refresh-dashboard-btn"><RefreshCw className={`w-4 h-4 ${fetching ? "animate-spin" : ""}`} /> Refresh</Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 bg-white/80 rounded-2xl p-1.5 border border-sky-100 mb-8 overflow-x-auto" data-testid="dashboard-tabs">
            {tabs.map(({ id, label, icon: TabIcon, count }) => (
              <button key={id} onClick={() => setActiveTab(id)} className={`flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-medium transition-all whitespace-nowrap ${activeTab === id ? "bg-[#1E56A0] text-white shadow-sm" : "text-slate-500 hover:text-[#1E56A0] hover:bg-sky-50"}`} data-testid={`tab-${id}`}>
                <TabIcon className="w-3.5 h-3.5" />{label}
                {count > 0 && <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${activeTab === id ? "bg-white/20" : "bg-sky-100 text-[#1E56A0]"}`}>{count}</span>}
              </button>
            ))}
          </div>

          {/* OVERVIEW */}
          {activeTab === "overview" && stats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3" data-testid="admin-stats">
              <StatCard icon={IndianRupee} label="Donations" value={stats.donations.total} sub={`\u20B9${stats.donations.total_amount.toLocaleString("en-IN")}`} color="#FF7F00" />
              <StatCard icon={CheckCircle} label="Confirmed" value={stats.donations.confirmed} color="#16A34A" />
              <StatCard icon={Users} label="Volunteers" value={stats.volunteers?.total || 0} color="#1E56A0" />
              <StatCard icon={Users} label="Members" value={stats.members?.total || 0} color="#7C3AED" />
              <StatCard icon={ArrowUpDown} label="Pending" value={stats.role_requests?.pending || 0} color="#F59E0B" />
              <StatCard icon={CalendarDays} label="Events" value={stats.drives?.total || 0} color="#059669" />
              <StatCard icon={Ticket} label="Tickets" value={stats.tickets?.total || 0} sub={`${stats.tickets?.open || 0} open`} color="#DC2626" />
              <StatCard icon={Shield} label="Verified PAN" value={stats.verification?.pan_verified || 0} sub={`${stats.verification?.pan_unverified || 0} unverified`} color="#0EA5E9" />
            </div>
          )}

          {/* DONATIONS */}
          {activeTab === "donations" && <DonationsPanel donations={donations} onStatusChange={handleStatusChange} />}

          {/* QUERIES */}
          {activeTab === "queries" && <QueriesPanel queries={queries} onStatusChange={handleStatusChange} />}

          {/* MESSAGES */}
          {activeTab === "messages" && <MessagesPanel threads={messageThreads} activeThread={activeAdminThread} threadMsgs={adminThreadMsgs} onLoadThread={loadAdminThread} onBack={() => setActiveAdminThread(null)} />}

          {/* TICKETS */}
          {activeTab === "tickets" && <TicketsPanel tickets={tickets} onStatusChange={handleTicketStatusChange} onRespond={handleTicketRespond} />}

          {/* ROLE REQUESTS */}
          {activeTab === "role-requests" && (
            <div className="space-y-3" data-testid="admin-role-requests">
              {roleRequests.length === 0 ? <p className="text-center text-slate-400 py-12">No role change requests.</p> :
                roleRequests.map(r => (
                  <div key={r.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`role-req-${r.id}`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-[#0D2847]">{r.name} <span className="text-xs text-slate-400">({r.email})</span></p>
                        <p className="text-xs mt-1"><span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${ROLE_COLORS[r.current_role] || ""}`}>{r.current_role}</span><span className="mx-2">&rarr;</span><span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${ROLE_COLORS[r.requested_role] || ""}`}>{r.requested_role}</span></p>
                        {r.reason && <p className="text-xs text-slate-400 mt-1 italic">"{r.reason}"</p>}
                      </div>
                      <div className="flex items-center gap-2">{r.status === "pending" ? (<><Button size="sm" onClick={() => handleRoleRequestAction(r.id, "approve")} className="bg-green-600 hover:bg-green-700 text-white text-xs rounded-lg h-8" data-testid={`approve-req-${r.id}`}><CheckCircle className="w-3 h-3 mr-1" />Approve</Button><Button size="sm" variant="outline" onClick={() => handleRoleRequestAction(r.id, "reject")} className="text-red-600 border-red-200 text-xs rounded-lg h-8" data-testid={`reject-req-${r.id}`}><XCircle className="w-3 h-3 mr-1" />Reject</Button></>) : <StatusBadge status={r.status} />}</div>
                    </div>
                  </div>
                ))
              }
            </div>
          )}

          {/* EVENTS / DRIVES */}
          {activeTab === "drives" && (
            <div data-testid="admin-drives">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Events & Drives</h2>
                <Button size="sm" onClick={() => setShowDriveForm(!showDriveForm)} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-lg gap-1" data-testid="add-drive-btn"><Plus className="w-4 h-4" /> Create Event</Button>
              </div>
              {showDriveForm && (
                <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 mb-4 space-y-3" data-testid="drive-form">
                  <div className="grid grid-cols-2 gap-3">
                    <Input placeholder="Event Title" value={driveForm.title} onChange={e => setDriveForm({...driveForm, title: e.target.value})} className="rounded-xl" data-testid="drive-title" />
                    <Input placeholder="Location" value={driveForm.location} onChange={e => setDriveForm({...driveForm, location: e.target.value})} className="rounded-xl" data-testid="drive-location" />
                  </div>
                  <Input placeholder="Description" value={driveForm.description} onChange={e => setDriveForm({...driveForm, description: e.target.value})} className="rounded-xl" data-testid="drive-description" />
                  <div className="grid grid-cols-4 gap-3">
                    <Input type="date" value={driveForm.date} onChange={e => setDriveForm({...driveForm, date: e.target.value})} className="rounded-xl" data-testid="drive-date" />
                    <Input type="text" placeholder="Time (optional)" value={driveForm.time} onChange={e => setDriveForm({...driveForm, time: e.target.value})} className="rounded-xl" data-testid="drive-time" />
                    <Input type="number" min={1} placeholder="Days" value={driveForm.estimated_days} onChange={e => setDriveForm({...driveForm, estimated_days: parseInt(e.target.value) || 1})} className="rounded-xl" data-testid="drive-days" />
                    <Select value={driveForm.mission_slug} onValueChange={val => setDriveForm({...driveForm, mission_slug: val})}><SelectTrigger className="rounded-xl" data-testid="drive-mission"><SelectValue placeholder="Mission Head..." /></SelectTrigger><SelectContent>{MISSIONS.map(m => <SelectItem key={m.slug} value={m.slug}>{m.name}</SelectItem>)}</SelectContent></Select>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleCreateDrive} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="save-drive-btn">Save Event</Button>
                    <Button variant="outline" onClick={() => setShowDriveForm(false)} className="rounded-xl">Cancel</Button>
                  </div>
                </div>
              )}
              {/* Pending reports alert */}
              {pendingEvents.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4" data-testid="pending-reports-alert">
                  <p className="text-sm font-medium text-red-800 flex items-center gap-2"><FileText className="w-4 h-4" /> {pendingEvents.length} event(s) need a report!</p>
                  {pendingEvents.map(d => (
                    <div key={d.id} className="flex items-center justify-between mt-2">
                      <span className="text-xs text-red-700">{d.title} — {new Date(d.date).toLocaleDateString("en-IN")}</span>
                      <Button size="sm" onClick={() => setShowEventReport(d)} className="bg-red-600 hover:bg-red-700 text-white text-xs rounded-lg h-7" data-testid={`report-btn-${d.id}`}>File Report</Button>
                    </div>
                  ))}
                </div>
              )}
              {drives.length === 0 ? <p className="text-center text-slate-400 py-12">No events yet.</p> : (
                <div className="space-y-3">
                  {["upcoming", "past"].map(type => { const filtered = drives.filter(d => d.drive_type === type); if (!filtered.length) return null; return (<div key={type}><h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">{type === "upcoming" ? "Upcoming" : "Past"}</h3>{filtered.map(d => (<div key={d.id} className={`bg-white rounded-xl border shadow-sm p-4 mb-2 ${type === "upcoming" ? "border-green-100" : "border-slate-100"}`} data-testid={`drive-${d.id}`}><div className="flex items-start justify-between"><div><p className="text-sm font-semibold text-[#0D2847]">{d.title} {d.reported && <span className="text-[10px] text-green-600 bg-green-50 px-2 py-0.5 rounded-full ml-2">Reported</span>}</p><p className="text-xs text-slate-500 mt-1">{d.description}</p><div className="flex gap-4 mt-2 text-xs text-slate-400"><span>{new Date(d.date).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span><span>{d.location}</span>{d.mission_slug && <span className="text-[#1E56A0]">{d.mission_slug}</span>}{d.time && <span>{d.time}</span>}</div></div><div className="flex gap-1">{!d.reported && type === "past" && <Button variant="ghost" size="sm" onClick={() => setShowEventReport(d)} className="text-[#1E56A0] hover:bg-sky-50" data-testid={`report-drive-${d.id}`}><FileText className="w-4 h-4" /></Button>}<Button variant="ghost" size="sm" onClick={() => handleDeleteDrive(d.id)} className="text-red-500 hover:bg-red-50" data-testid={`delete-drive-${d.id}`}><Trash2 className="w-4 h-4" /></Button></div></div></div>))}</div>); })}
                </div>
              )}
            </div>
          )}

          {/* EMAIL BLAST */}
          {activeTab === "email-blast" && (
            <div data-testid="admin-email-blast">
              <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-6 mb-6" data-testid="blast-form">
                <h2 className="text-lg font-semibold text-[#0D2847] mb-4" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Send Email Blast</h2>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <Input placeholder="Subject" value={blastForm.subject} onChange={e => setBlastForm({...blastForm, subject: e.target.value})} className="rounded-xl" data-testid="blast-subject" />
                    <Select value={blastForm.target} onValueChange={val => setBlastForm({...blastForm, target: val})}><SelectTrigger className="rounded-xl" data-testid="blast-target"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="all">All Users</SelectItem><SelectItem value="volunteers">Volunteers Only</SelectItem><SelectItem value="members">Members Only</SelectItem></SelectContent></Select>
                  </div>
                  <textarea placeholder="Email body (HTML supported)..." value={blastForm.body} onChange={e => setBlastForm({...blastForm, body: e.target.value})} rows={5} className="w-full text-sm border border-sky-100 rounded-xl px-3 py-2 resize-none" data-testid="blast-body" />
                  <Button onClick={handleSendBlast} disabled={blastSending} className="bg-[#FF7F00] hover:bg-[#E06F00] text-white rounded-xl gap-2" data-testid="send-blast-btn"><Mail className="w-4 h-4" /> {blastSending ? "Sending..." : "Send Email Blast"}</Button>
                </div>
              </div>
              {emailBlasts.length > 0 && (
                <div className="space-y-3"><h3 className="text-sm font-semibold text-slate-500 mb-2">Previous Blasts</h3>
                  {emailBlasts.map(b => (<div key={b.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4"><div className="flex items-center justify-between"><div><p className="text-sm font-medium text-[#0D2847]">{b.subject}</p><p className="text-xs text-slate-400">To: {b.target} | Sent: {b.sent_count}/{b.recipient_count} | By: {b.sent_by}</p></div><p className="text-[10px] text-slate-400">{new Date(b.created_at).toLocaleDateString("en-IN")}</p></div></div>))}
                </div>
              )}
            </div>
          )}

          {/* ADMIN PROMOTIONS */}
          {activeTab === "promotions" && (
            <div data-testid="admin-promotions">
              <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-6 mb-6">
                <h2 className="text-lg font-semibold text-[#0D2847] mb-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>Current Admins</h2>
                <div className="flex flex-wrap gap-2 mb-4">{admins.map(a => (<span key={a.email} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200"><Shield className="w-3 h-3" />{a.name} ({a.email})</span>))}</div>
                <h3 className="text-sm font-semibold text-slate-500 mb-2">Promote a user to Admin</h3>
                <p className="text-xs text-slate-400 mb-3">Requires approval from {Math.max(1, admins.length - 1)} other admin(s).</p>
                <div className="flex gap-2">
                  <Input placeholder="Email to promote" value={promoteEmail} onChange={e => setPromoteEmail(e.target.value)} className="flex-1 rounded-xl" data-testid="promote-email" />
                  <Input placeholder="Reason" value={promoteReason} onChange={e => setPromoteReason(e.target.value)} className="flex-1 rounded-xl" data-testid="promote-reason" />
                  <Button onClick={handlePromote} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl" data-testid="promote-btn">Request Promotion</Button>
                </div>
              </div>
              {promotionRequests.length > 0 && (
                <div className="space-y-3">
                  {promotionRequests.map(r => (
                    <div key={r.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`promo-${r.id}`}>
                      <div className="flex items-center justify-between">
                        <div><p className="text-sm font-medium text-[#0D2847]">{r.target_name} <span className="text-xs text-slate-400">({r.target_email})</span></p><p className="text-xs text-slate-500">By: {r.requested_by} | Approvals: {r.approvals?.length || 0}/{r.required_approvals} {r.reason && `| "${r.reason}"`}</p></div>
                        <div className="flex items-center gap-2">{r.status === "pending" ? (<><Button size="sm" onClick={() => handlePromotionAction(r.id, "approve")} className="bg-green-600 text-white text-xs rounded-lg h-8" data-testid={`approve-promo-${r.id}`}><CheckCircle className="w-3 h-3 mr-1" />Approve</Button><Button size="sm" variant="outline" onClick={() => handlePromotionAction(r.id, "reject")} className="text-red-600 border-red-200 text-xs rounded-lg h-8" data-testid={`reject-promo-${r.id}`}><XCircle className="w-3 h-3 mr-1" />Reject</Button></>) : <StatusBadge status={r.status} />}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* PATRONS / SUBSCRIPTIONS */}
          {activeTab === "patrons" && (
            <div data-testid="admin-patrons">
              <div className="bg-gradient-to-br from-fuchsia-50 to-amber-50 rounded-2xl border border-fuchsia-200 shadow-sm p-6 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-[#0D2847] flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                      <Crown className="w-5 h-5 text-fuchsia-600" /> Heroic Patrons
                    </h2>
                    <p className="text-xs text-slate-500 mt-1">Recurring donors auto-promoted after 6 successful charges. Surfaced publicly on the Wall of Fame.</p>
                  </div>
                  <Button onClick={handleRecomputePatrons} className="bg-fuchsia-600 hover:bg-fuchsia-700 text-white rounded-xl gap-2" data-testid="recompute-patrons-btn">
                    <RefreshCw className="w-4 h-4" /> Recompute
                  </Button>
                </div>
              </div>

              {/* Webhook Health Widget */}
              {webhookHealth && (
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-5 mb-6" data-testid="webhook-health-widget">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-semibold text-[#0D2847] flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                      <Activity className={`w-4 h-4 ${webhookHealth.pass_rate >= 90 ? "text-green-600" : webhookHealth.pass_rate >= 50 ? "text-amber-500" : "text-red-500"}`} />
                      Razorpay Webhook Health
                    </h3>
                    <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${webhookHealth.pass_rate >= 90 ? "bg-green-50 text-green-700 border-green-200" : webhookHealth.pass_rate >= 50 ? "bg-amber-50 text-amber-700 border-amber-200" : "bg-red-50 text-red-700 border-red-200"}`} data-testid="webhook-pass-rate">
                      {webhookHealth.pass_rate}% verified
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                    <div className="bg-sky-50/50 rounded-xl p-3"><p className="text-[10px] text-slate-500 uppercase tracking-wider">Total Events</p><p className="text-xl font-semibold text-[#0D2847]">{webhookHealth.total}</p></div>
                    <div className="bg-green-50/50 rounded-xl p-3"><p className="text-[10px] text-slate-500 uppercase tracking-wider">Verified</p><p className="text-xl font-semibold text-green-700" data-testid="webhook-verified-count">{webhookHealth.verified}</p></div>
                    <div className="bg-red-50/50 rounded-xl p-3"><p className="text-[10px] text-slate-500 uppercase tracking-wider">Unverified</p><p className="text-xl font-semibold text-red-600" data-testid="webhook-unverified-count">{webhookHealth.unverified}</p></div>
                    <div className="bg-amber-50/50 rounded-xl p-3"><p className="text-[10px] text-slate-500 uppercase tracking-wider">Last Verified</p><p className="text-xs font-medium text-[#0D2847]">{webhookHealth.last_verified ? new Date(webhookHealth.last_verified.received_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "—"}</p></div>
                  </div>
                  {webhookHealth.unverified > 0 && webhookHealth.verified === 0 && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-3 mb-3 text-xs text-red-700">
                      <strong>⚠️ No verified events yet.</strong> Check that <code className="bg-red-100 px-1 rounded">RAZORPAY_WEBHOOK_SECRET</code> in <code className="bg-red-100 px-1 rounded">.env</code> matches the secret you set in the Razorpay dashboard.
                    </div>
                  )}
                  {webhookHealth.recent.length === 0 ? (
                    <p className="text-center text-slate-400 py-4 text-xs">No webhook events received yet. Razorpay will deliver the first event when a subscription gets charged.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs" data-testid="webhook-events-table">
                        <thead className="border-b border-sky-100">
                          <tr>
                            <th className="text-left py-2 text-slate-500 font-medium">Time</th>
                            <th className="text-left py-2 text-slate-500 font-medium">Event</th>
                            <th className="text-left py-2 text-slate-500 font-medium">Status</th>
                            <th className="text-right py-2 text-slate-500 font-medium">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {webhookHealth.recent.map(e => (
                            <tr key={e.id} className="border-b border-sky-50 hover:bg-sky-50/30" data-testid={`webhook-event-${e.id}`}>
                              <td className="py-2 text-slate-400 whitespace-nowrap">{new Date(e.received_at).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</td>
                              <td className="py-2"><span className="px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100 text-[10px] font-medium">{e.event}</span></td>
                              <td className="py-2">
                                {e.verified
                                  ? <span className="inline-flex items-center gap-1 text-green-700"><CheckCircle className="w-3 h-3" />verified</span>
                                  : <span className="inline-flex items-center gap-1 text-red-600"><XCircle className="w-3 h-3" />unverified</span>}
                                {e.replayed_at && <span className="ml-2 text-[10px] text-amber-600">↻ replayed</span>}
                              </td>
                              <td className="py-2 text-right">
                                <button onClick={() => handleReplayWebhook(e.id)} className="text-[10px] px-2 py-1 rounded-lg bg-amber-50 text-amber-700 hover:bg-amber-100 border border-amber-200 font-medium" data-testid={`replay-webhook-${e.id}`}>Replay</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">All Subscriptions ({subscriptions.length})</h3>
              {subscriptions.length === 0 ? (
                <p className="text-center text-slate-400 py-12">No recurring subscriptions yet. Donors can opt-in from the Donate page.</p>
              ) : (
                <div className="space-y-2">
                  {subscriptions.map(s => (
                    <div key={s.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`subscription-${s.id}`}>
                      <div className="flex items-center justify-between flex-wrap gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-[#0D2847]">
                            {s.name} <span className="text-xs text-slate-400">({s.email})</span>
                            {s.status === "cancelled" && <span className="text-[10px] text-red-500 ml-2">[CANCELLED]</span>}
                          </p>
                          <p className="text-xs text-slate-500 flex flex-wrap items-center gap-3 mt-1">
                            <span className="inline-flex items-center gap-1"><Repeat className="w-3 h-3" /> {s.plan}</span>
                            <span><IndianRupee className="w-3 h-3 inline" />{s.amount?.toLocaleString("en-IN")}</span>
                            <span className={`px-2 py-0.5 rounded-full border font-medium text-[10px] ${s.mode === "live" ? "bg-green-50 text-green-700 border-green-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>
                              {s.mode === "live" ? "LIVE" : "STUB"}
                            </span>
                            <span className="text-[10px] text-slate-400">{new Date(s.created_at).toLocaleDateString("en-IN")}</span>
                          </p>
                        </div>
                        {s.status !== "cancelled" && (
                          <Button size="sm" onClick={() => handleSimulateCharge(s.id)} className="bg-amber-500 hover:bg-amber-600 text-white text-xs rounded-lg h-8 gap-1" data-testid={`simulate-charge-${s.id}`}>
                            <Plus className="w-3 h-3" /> Simulate Charge
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ARTICLES */}
          {activeTab === "articles" && (
            <div className="space-y-4" data-testid="admin-articles">
              {eventReports.length === 0 ? <p className="text-center text-slate-400 py-12">No event articles yet. File an event report to generate one.</p> :
                eventReports.map(r => (<ArticleCard key={r.id} report={r} />))
              }
            </div>
          )}

          {/* ROSTER */}
          {activeTab === "roster" && (
            <div data-testid="admin-users-list">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <span className="text-xs text-slate-500 font-medium">Role:</span>
                {["all", "admin", "volunteer", "member"].map(r => (<button key={r} onClick={() => setRoleFilter(r)} className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${roleFilter === r ? "bg-[#1E56A0] text-white border-[#1E56A0]" : "bg-white text-slate-500 border-sky-100 hover:bg-sky-50"}`} data-testid={`filter-${r}`}>{r === "all" ? `All (${users.length})` : `${r.charAt(0).toUpperCase() + r.slice(1)} (${users.filter(u => u.role === r).length})`}</button>))}
              </div>
              <div className="flex flex-wrap items-center gap-2 mb-4" data-testid="spec-filter-row">
                <span className="text-xs text-slate-500 font-medium">Specialization:</span>
                <button onClick={() => setSpecFilter("all")} className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${specFilter === "all" ? "bg-[#FF7F00] text-white border-[#FF7F00]" : "bg-white text-slate-500 border-amber-100 hover:bg-amber-50"}`} data-testid="spec-filter-all">All</button>
                {SPECIALIZATIONS.map(s => {
                  const cnt = users.filter(u => (u.specializations || []).includes(s.key)).length;
                  return (
                    <button key={s.key} onClick={() => setSpecFilter(s.key)} className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-colors ${specFilter === s.key ? "bg-[#FF7F00] text-white border-[#FF7F00]" : "bg-white text-slate-500 border-amber-100 hover:bg-amber-50"}`} data-testid={`spec-filter-${s.key}`}>
                      {s.label} {cnt > 0 && <span className="text-[10px] opacity-70 ml-1">({cnt})</span>}
                    </button>
                  );
                })}
              </div>
              <div className="space-y-3">{filteredUsers.length === 0 ? <p className="text-center text-slate-400 py-12">No users matching filters.</p> : filteredUsers.map(u => (<UserCard key={u.email} u={u} onDelete={handleDeleteUser} onUpdate={handleAdminUpdateUser} onAddBadge={handleAddBadge} onRemoveBadge={handleRemoveBadge} onVerifyPan={handleVerifyPan} isOnWall={wallOfFame.some(w => w.email === u.email)} onToggleWall={handleToggleWallOfFame} />))}</div>
            </div>
          )}

          {/* ACTIVITY LOG */}
          {activeTab === "activity" && (
            <div className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden" data-testid="admin-activity-log">
              <div className="max-h-[70vh] overflow-y-auto">
                {activityLogs.length === 0 ? <p className="text-center text-slate-400 py-12">No activity.</p> :
                  <table className="w-full text-xs"><thead className="sticky top-0 bg-sky-50 border-b border-sky-100"><tr><th className="text-left p-3 text-slate-500 font-medium">Time</th><th className="text-left p-3 text-slate-500 font-medium">Action</th><th className="text-left p-3 text-slate-500 font-medium">User</th><th className="text-left p-3 text-slate-500 font-medium">Details</th></tr></thead>
                    <tbody>{activityLogs.map((log, i) => (<tr key={log.id || i} className="border-b border-sky-50 hover:bg-sky-50/30"><td className="p-3 text-slate-400 whitespace-nowrap">{new Date(log.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}</td><td className="p-3"><span className="px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100 font-medium">{log.action}</span></td><td className="p-3 text-slate-600">{log.user_email || "—"}</td><td className="p-3 text-slate-500 max-w-xs truncate">{log.details}</td></tr>))}</tbody>
                  </table>}
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

// ── Sub-components ──
function ArticleCard({ report }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-5" data-testid={`article-${report.id}`}>
      <div className="flex items-start justify-between cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div><p className="text-base font-semibold text-[#0D2847]">{report.drive_title}</p><p className="text-xs text-slate-400 mt-1">{new Date(report.created_at).toLocaleDateString("en-IN")} | Star Hero: <span className="text-[#FF7F00] font-medium">{report.star_hero_name}</span></p><p className="text-xs text-slate-500 mt-1">Volunteers: {report.volunteer_names?.join(", ") || "—"}</p></div>
        {expanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
      </div>
      {expanded && (<div className="mt-4 p-4 bg-sky-50/50 rounded-xl"><p className="text-sm text-[#0D2847] whitespace-pre-wrap leading-relaxed">{report.article}</p><div className="grid grid-cols-3 gap-3 mt-4 text-xs"><div><span className="text-slate-400">Time:</span> <span className="text-slate-700">{report.time_spent}</span></div><div><span className="text-slate-400">Resources:</span> <span className="text-slate-700">{report.resources_spent}</span></div><div><span className="text-slate-400">Rating:</span> <span className="text-slate-700">{report.admin_rating}/10</span></div></div>{report.issues && <p className="text-xs text-red-600 mt-2">Issues: {report.issues}</p>}</div>)}
    </div>
  );
}

function DonationsPanel({ donations, onStatusChange }) {
  const [expandedId, setExpandedId] = useState(null);
  if (!donations.length) return <p className="text-center text-slate-400 py-12">No donations.</p>;
  return (<div className="space-y-3" data-testid="admin-donations-list">{donations.map(d => (<div key={d.id} className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden"><div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30" onClick={() => setExpandedId(expandedId === d.id ? null : d.id)}><div className="flex items-center gap-4 min-w-0"><div className="w-9 h-9 rounded-full bg-[#FF7F00]/10 flex items-center justify-center shrink-0"><IndianRupee className="w-4 h-4 text-[#FF7F00]" /></div><div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{d.name}</p><p className="text-xs text-slate-400">{d.email}</p></div></div><div className="flex items-center gap-4 shrink-0"><span className="text-sm font-semibold">{"\u20B9"}{d.amount?.toLocaleString("en-IN")}</span><StatusBadge status={d.status} /></div></div>
    {expandedId === d.id && (<div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2"><div className="grid grid-cols-3 gap-3 text-xs"><div><span className="text-slate-400">PAN:</span> {d.pan_number || "—"}</div><div><span className="text-slate-400">Aadhaar:</span> {d.aadhaar_number || "—"}</div><div><span className="text-slate-400">Date:</span> {new Date(d.created_at).toLocaleDateString("en-IN")}</div></div>
    <div className="flex items-center gap-2 pt-1"><Select value={d.status} onValueChange={val => onStatusChange("donations", d.id, val)}><SelectTrigger className="h-7 text-xs w-32 rounded-lg"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="rejected">Rejected</SelectItem></SelectContent></Select>
    {d.pan_number && <a href={`${process.env.REACT_APP_BACKEND_URL}/api/donations/${d.id}/certificate`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium bg-[#FF7F00]/10 text-[#FF7F00] hover:bg-[#FF7F00]/20" data-testid={`download-cert-${d.id}`}><Download className="w-3 h-3" /> 80G</a>}</div></div>)}</div>))}</div>);
}

function QueriesPanel({ queries, onStatusChange }) {
  const [expandedId, setExpandedId] = useState(null);
  if (!queries.length) return <p className="text-center text-slate-400 py-12">No queries.</p>;
  return (<div className="space-y-3" data-testid="admin-queries-list">{queries.map(q => (<div key={q.id} className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden"><div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30" onClick={() => setExpandedId(expandedId === q.id ? null : q.id)}><div className="flex items-center gap-4 min-w-0"><div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0"><MessageSquare className="w-4 h-4 text-[#28A9E2]" /></div><div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{q.subject}</p><p className="text-xs text-slate-400">{q.name}</p></div></div><StatusBadge status={q.status} /></div>
    {expandedId === q.id && (<div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-2"><p className="text-xs text-slate-600 bg-sky-50/50 rounded-lg p-3">{q.message}</p><Select value={q.status} onValueChange={val => onStatusChange("queries", q.id, val)}><SelectTrigger className="h-7 text-xs w-32 rounded-lg"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="open">Open</SelectItem><SelectItem value="responded">Responded</SelectItem><SelectItem value="closed">Closed</SelectItem></SelectContent></Select></div>)}</div>))}</div>);
}

function MessagesPanel({ threads, activeThread, threadMsgs, onLoadThread, onBack }) {
  if (activeThread) return (<div data-testid="admin-messages-list"><button onClick={onBack} className="flex items-center gap-2 text-sm text-[#1E56A0] mb-4"><Eye className="w-4 h-4" /> Back</button><div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 mb-4"><p className="text-sm font-medium">{activeThread.senderName} &harr; {activeThread.recipientName}</p></div><div className="space-y-3 max-h-[60vh] overflow-y-auto">{threadMsgs.map(m => (<div key={m.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4"><div className="flex justify-between mb-1"><p className="text-xs font-medium text-[#1E56A0]">{m.sender_name}</p><p className="text-[10px] text-slate-400">{new Date(m.created_at).toLocaleString("en-IN")}</p></div><p className="text-sm whitespace-pre-wrap">{m.message}</p></div>))}</div></div>);
  return (<div className="space-y-3" data-testid="admin-messages-list">{threads.length === 0 ? <p className="text-center text-slate-400 py-12">No threads.</p> : threads.map((t, i) => (<div key={i} onClick={() => onLoadThread(t.sender_email, t.recipient_email, t.sender, t.recipient)} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 flex items-center justify-between cursor-pointer hover:shadow-md" data-testid={`admin-thread-${i}`}><div className="flex items-center gap-4 min-w-0"><div className="w-9 h-9 rounded-full bg-[#28A9E2]/10 flex items-center justify-center shrink-0"><MessageCircle className="w-4 h-4 text-[#28A9E2]" /></div><div className="min-w-0"><p className="text-sm font-medium truncate">{t.sender} &harr; {t.recipient}</p><p className="text-xs text-slate-400 truncate">{t.last_message?.slice(0, 60)}</p></div></div><span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#28A9E2] text-white">{t.count}</span></div>))}</div>);
}

function TicketsPanel({ tickets, onStatusChange, onRespond }) {
  if (!tickets.length) return <p className="text-center text-slate-400 py-12">No tickets.</p>;
  return (<div className="space-y-3" data-testid="admin-tickets-list">{tickets.map(tk => (<div key={tk.id} className="bg-white rounded-xl border border-sky-100 shadow-sm p-4" data-testid={`admin-ticket-${tk.id}`}><div className="flex items-start justify-between mb-2"><div><p className="text-sm font-medium">{tk.subject}</p><p className="text-xs text-slate-400">{tk.user_name} | {new Date(tk.created_at).toLocaleDateString("en-IN")}</p></div><div className="flex items-center gap-2"><span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${tk.priority === "high" ? "bg-red-50 text-red-700 border-red-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>{tk.priority}</span><Select value={tk.status} onValueChange={val => onStatusChange(tk.id, val)}><SelectTrigger className="h-6 text-[10px] w-28 rounded-lg"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="open">Open</SelectItem><SelectItem value="in-progress">In Progress</SelectItem><SelectItem value="responded">Responded</SelectItem><SelectItem value="resolved">Resolved</SelectItem><SelectItem value="closed">Closed</SelectItem></SelectContent></Select></div></div><p className="text-xs text-slate-600 mb-2">{tk.description}</p>{tk.admin_response && <div className="bg-sky-50 border border-sky-200 rounded-lg p-2 mb-2"><p className="text-[10px] font-medium text-[#1E56A0]">Response:</p><p className="text-xs">{tk.admin_response}</p></div>}<button onClick={() => onRespond(tk.id, window.prompt("Response:"))} className="text-xs text-[#1E56A0] hover:underline">{tk.admin_response ? "Update" : "Respond"}</button></div>))}</div>);
}

function UserCard({ u, onDelete, onUpdate, onAddBadge, onRemoveBadge, onVerifyPan, isOnWall, onToggleWall }) {
  const [expanded, setExpanded] = useState(false);
  const [hours, setHours] = useState(u.volunteer_hours || 0);
  const [comments, setComments] = useState(u.admin_comments || "");
  const [suspendReason, setSuspendReason] = useState("");
  const [suspendUntil, setSuspendUntil] = useState("");
  const [removeReason, setRemoveReason] = useState("");
  const [showRemove, setShowRemove] = useState(false);
  const [newBadge, setNewBadge] = useState("");
  const BADGES = ["Star Volunteer of the Month", "Star Volunteer of the Quarter", "Star Volunteer of the Year", "Top Donor", "Rising Star", "Community Builder"];
  const handleSuspend = () => {
    if (suspendReason.trim().length < 5) { toast.error("Please enter a suspension reason (min 5 chars)"); return; }
    if (window.confirm(`Suspend ${u.name}?\nReason: ${suspendReason}`)) {
      onUpdate(u.email, { status: "suspended", suspension_reason: suspendReason.trim(), suspended_until: suspendUntil });
      setSuspendReason(""); setSuspendUntil("");
    }
  };
  const handleRemoveConfirm = () => {
    if (removeReason.trim().length < 5) { toast.error("Removal reason is required (min 5 chars)"); return; }
    onDelete(u.email, removeReason.trim());
    setRemoveReason(""); setShowRemove(false);
  };
  return (
    <div className="bg-white rounded-xl border border-sky-100 shadow-sm overflow-hidden" data-testid={`admin-user-${u.email}`}>
      <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-sky-50/30" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3 min-w-0"><div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${u.status === "suspended" ? "bg-red-100" : "bg-[#1E56A0]/10"}`}><UserCog className={`w-4 h-4 ${u.status === "suspended" ? "text-red-500" : "text-[#1E56A0]"}`} /></div><div className="min-w-0"><p className="text-sm font-medium text-[#0D2847] truncate">{u.name}{u.status === "suspended" && <span className="text-xs text-red-500 ml-1">[SUSPENDED]</span>}{u.pan_verified && <span className="text-[10px] text-green-600 ml-1" title="PAN verified">✓PAN</span>}</p><p className="text-xs text-slate-400">{u.email} {u.specializations?.length > 0 && `| ${u.specializations.join(", ")}`}</p></div></div>
        <div className="flex items-center gap-2 shrink-0"><span className="text-xs text-slate-400">{u.volunteer_hours || 0}h</span>{u.merchandise_issued && <Package className="w-3 h-3 text-green-500" />}<span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${ROLE_COLORS[u.role] || ROLE_COLORS.member}`}>{u.role}</span><Eye className="w-4 h-4 text-slate-300" /></div>
      </div>
      {expanded && (
        <div className="px-4 pb-4 border-t border-sky-50 pt-3 space-y-3">
          {u.status === "suspended" && u.suspension_reason && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-2 text-xs" data-testid={`suspension-info-${u.email}`}>
              <p className="font-medium text-red-700">Suspended: <span className="font-normal">{u.suspension_reason}</span></p>
              {u.suspended_until && <p className="text-red-600">Until: {u.suspended_until}</p>}
              {u.suspended_by && <p className="text-red-500 text-[10px]">By: {u.suspended_by}</p>}
            </div>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">{u.pan_number && <div><span className="text-slate-400">PAN:</span> {u.pan_number} {u.pan_verified ? <span className="text-green-600">(Verified)</span> : <span className="text-red-500">(Unverified)</span>}</div>}{u.aadhaar_number && <div><span className="text-slate-400">Aadhaar:</span> {u.aadhaar_number}</div>}{u.address && <div className="col-span-2"><span className="text-slate-400">Address:</span> {u.address}</div>}</div>
          {u.role === "volunteer" && (<><div><p className="text-xs font-medium text-slate-500 mb-1 flex items-center gap-1"><Award className="w-3 h-3" /> Badges</p><div className="flex flex-wrap gap-1 mb-2">{(u.badges || []).map(b => (<span key={b} className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-sky-50 text-[#1E56A0] border border-sky-100">{b}<button onClick={() => onRemoveBadge(u.email, b)} className="text-red-400 hover:text-red-600">&times;</button></span>))}</div><div className="flex gap-1"><select value={newBadge} onChange={e => setNewBadge(e.target.value)} className="text-xs border rounded-lg px-2 py-1"><option value="">Add badge...</option>{BADGES.filter(b => !(u.badges || []).includes(b)).map(b => <option key={b} value={b}>{b}</option>)}</select>{newBadge && <button onClick={() => { onAddBadge(u.email, newBadge); setNewBadge(""); }} className="text-xs text-[#1E56A0]">Add</button>}</div></div>
          <div className="flex flex-wrap items-end gap-4"><div><label className="text-xs text-slate-400 block mb-1">Hours</label><div className="flex gap-1"><input type="number" value={hours} onChange={e => setHours(parseInt(e.target.value) || 0)} className="w-20 text-xs border rounded-lg px-2 py-1" /><button onClick={() => onUpdate(u.email, { volunteer_hours: hours })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg">Save</button></div></div><label className="flex items-center gap-2 text-xs cursor-pointer"><input type="checkbox" checked={u.merchandise_issued || false} onChange={e => onUpdate(u.email, { merchandise_issued: e.target.checked })} className="rounded" /><Package className="w-3 h-3" /> Merch</label></div></>)}
          <div><label className="text-xs text-slate-400 block mb-1">Comments</label><div className="flex gap-1"><textarea value={comments} onChange={e => setComments(e.target.value)} rows={2} className="flex-1 text-xs border rounded-lg px-2 py-1 resize-none" /><button onClick={() => onUpdate(u.email, { admin_comments: comments })} className="text-xs px-2 py-1 bg-[#1E56A0] text-white rounded-lg self-end">Save</button></div></div>
          <div className="flex flex-wrap gap-2 pt-2 border-t border-sky-50">
            {u.role !== "admin" && <Select onValueChange={val => { if (window.confirm(`Change role to ${val}?`)) onUpdate(u.email, { role: val }); }}><SelectTrigger className="h-8 text-xs w-40 rounded-lg"><SelectValue placeholder="Change role..." /></SelectTrigger><SelectContent>{u.role !== "volunteer" && <SelectItem value="volunteer">Volunteer</SelectItem>}{u.role !== "member" && <SelectItem value="member">Member</SelectItem>}</SelectContent></Select>}
            {u.pan_number && <button onClick={() => onVerifyPan(u.email)} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-sky-50 text-[#1E56A0] hover:bg-sky-100 border border-sky-200" data-testid={`verify-pan-${u.email}`}><Shield className="w-3 h-3" />{u.pan_verified ? "Re-verify PAN" : "Verify PAN"}</button>}
            {u.status !== "suspended" ? (
              <div className="flex items-center gap-1 flex-wrap" data-testid={`suspend-row-${u.email}`}>
                <input placeholder="Suspension reason*" value={suspendReason} onChange={e => setSuspendReason(e.target.value)} className="text-xs border rounded-lg px-2 py-1 w-44" data-testid={`suspend-reason-${u.email}`} />
                <input type="date" value={suspendUntil} onChange={e => setSuspendUntil(e.target.value)} className="text-xs border rounded-lg px-2 py-1 w-32" data-testid={`suspend-until-${u.email}`} />
                <button onClick={handleSuspend} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100" data-testid={`suspend-btn-${u.email}`}><PauseCircle className="w-3 h-3" />Suspend</button>
              </div>
            ) : (
              <button onClick={() => { if (window.confirm(`Restore ${u.name}'s account?`)) onUpdate(u.email, { status: "active" }); }} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-green-50 text-green-700 hover:bg-green-100" data-testid={`unsuspend-btn-${u.email}`}><PlayCircle className="w-3 h-3" />Unsuspend</button>
            )}
            <button onClick={() => setShowRemove(!showRemove)} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100" data-testid={`remove-btn-${u.email}`}><Trash2 className="w-3 h-3" />Remove</button>
            <button onClick={() => onToggleWall(u.email, isOnWall)} className={`inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg ${isOnWall ? "bg-amber-100 text-amber-800 border border-amber-300" : "bg-amber-50 text-amber-600"}`}><Star className={`w-3 h-3 ${isOnWall ? "fill-amber-500" : ""}`} />{isOnWall ? "On Wall" : "Add Wall"}</button>
          </div>
          {showRemove && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 mt-2" data-testid={`remove-confirm-${u.email}`}>
              <p className="text-xs font-medium text-red-700 mb-2">⚠️ Remove {u.name} ({u.email})? This is logged with your reason.</p>
              <div className="flex gap-2">
                <input placeholder="Reason for removal (min 5 chars)*" value={removeReason} onChange={e => setRemoveReason(e.target.value)} className="flex-1 text-xs border border-red-300 rounded-lg px-2 py-1.5" data-testid={`remove-reason-${u.email}`} />
                <button onClick={handleRemoveConfirm} className="text-xs px-3 py-1.5 rounded-lg bg-red-600 text-white hover:bg-red-700" data-testid={`remove-confirm-btn-${u.email}`}>Confirm Remove</button>
                <button onClick={() => { setShowRemove(false); setRemoveReason(""); }} className="text-xs px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:bg-slate-50">Cancel</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
