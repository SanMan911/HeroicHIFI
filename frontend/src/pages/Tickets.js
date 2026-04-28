import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import api, { formatApiError } from "../lib/api";
import { formatDate } from "../lib/dates";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { motion } from "framer-motion";
import { Ticket, Plus, Clock, CheckCircle, MessageCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

const STATUS_STYLES = {
  open: "bg-yellow-100 text-yellow-800 border-yellow-200",
  responded: "bg-blue-100 text-blue-800 border-blue-200",
  "in-progress": "bg-orange-100 text-orange-800 border-orange-200",
  resolved: "bg-green-100 text-green-800 border-green-200",
  closed: "bg-slate-100 text-slate-600 border-slate-200",
};

export default function Tickets() {
  const { user, loading: authLoading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].tickets;
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ subject: "", description: "", priority: "medium" });
  const [submitting, setSubmitting] = useState(false);

  const fetchTickets = useCallback(async () => {
    try {
      const { data } = await api.get("/tickets");
      setTickets(data);
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) fetchTickets(); }, [user, fetchTickets]);

  if (authLoading) return null;
  if (!user) return <Navigate to="/login" replace />;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.subject || !form.description) { toast.error(t.fill_required); return; }
    setSubmitting(true);
    try {
      const { data } = await api.post("/tickets", form);
      toast.success(data.message);
      setForm({ subject: "", description: "", priority: "medium" });
      setShowForm(false);
      fetchTickets();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSubmitting(false); }
  };

  return (
    <div data-testid="tickets-page">
      <section className="relative py-16 sm:py-20 bg-[#0D2847]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-4">
            <Ticket className="w-7 h-7 text-white" />
          </motion.div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.title}
          </h1>
          <p className="text-sm sm:text-base text-stone-400 mt-2">{t.subtitle}</p>
        </div>
      </section>

      <section className="py-8 sm:py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="flex justify-end mb-6">
            <Button onClick={() => setShowForm(!showForm)} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full gap-2" data-testid="new-ticket-btn">
              <Plus className="w-4 h-4" /> {showForm ? t.cancel : t.new_ticket}
            </Button>
          </div>

          {showForm && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 mb-6">
              <form onSubmit={handleSubmit} className="space-y-4" data-testid="ticket-form">
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.subject} *</Label>
                  <Input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} className="mt-1 rounded-xl" data-testid="ticket-subject" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.description} *</Label>
                  <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={4} className="mt-1 rounded-xl" data-testid="ticket-description" required />
                </div>
                <div>
                  <Label className="text-sm font-medium text-slate-700">{t.priority}</Label>
                  <Select value={form.priority} onValueChange={(val) => setForm({ ...form, priority: val })}>
                    <SelectTrigger className="mt-1 rounded-xl" data-testid="ticket-priority">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">{t.low}</SelectItem>
                      <SelectItem value="medium">{t.medium}</SelectItem>
                      <SelectItem value="high">{t.high}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button type="submit" disabled={submitting} className="bg-[#FF7F00] hover:bg-[#E06B00] text-white rounded-full px-6" data-testid="submit-ticket-btn">
                  {submitting ? "..." : t.submit}
                </Button>
              </form>
            </motion.div>
          )}

          {loading ? <p className="text-center text-slate-400 py-8">{t.loading}</p> :
           tickets.length === 0 ? (
             <div className="text-center py-12">
               <Ticket className="w-10 h-10 text-slate-300 mx-auto mb-3" />
               <p className="text-slate-400">{t.no_tickets}</p>
             </div>
           ) : (
             <div className="space-y-4" data-testid="tickets-list">
               {tickets.map((tk) => (
                 <motion.div key={tk.id} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                   className="bg-white rounded-2xl border border-sky-100 shadow-sm p-5" data-testid={`ticket-${tk.id}`}>
                   <div className="flex items-start justify-between mb-3">
                     <div>
                       <h3 className="text-base font-medium text-[#0D2847]">{tk.subject}</h3>
                       <p className="text-xs text-slate-400">{formatDate(tk.created_at)} &middot; {t[tk.priority] || tk.priority}</p>
                     </div>
                     <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_STYLES[tk.status] || STATUS_STYLES.open}`}>
                       {tk.status}
                     </span>
                   </div>
                   <p className="text-sm text-slate-600 mb-3 whitespace-pre-wrap">{tk.description}</p>
                   {tk.admin_response && (
                     <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 mt-2">
                       <p className="text-xs font-medium text-[#1E56A0] mb-1 flex items-center gap-1"><MessageCircle className="w-3 h-3" /> {t.admin_response}</p>
                       <p className="text-sm text-[#0D2847]">{tk.admin_response}</p>
                     </div>
                   )}
                 </motion.div>
               ))}
             </div>
           )}
        </div>
      </section>
    </div>
  );
}
