import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import api, { formatApiError } from "../lib/api";
import { formatDate } from "../lib/dates";
import { Input } from "../components/ui/input";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { Users, Search, Send, ArrowLeft, MessageCircle, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

function MemberCard({ member, onConnect, t }) {
  const interests = member.interests || [];
  const badges = member.badges || [];
  return (
    <div className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow" data-testid={`member-${member.email}`}>
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-10 h-10 rounded-full bg-[#1E56A0]/10 flex items-center justify-center shrink-0 text-[#1E56A0] font-semibold text-sm" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
          {member.name?.charAt(0)?.toUpperCase() || "?"}
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-[#0D2847] truncate">{member.name}</p>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>{member.role === "admin" ? t.admin_role : t.volunteer_role}</span>
            {(member.volunteer_hours || 0) > 0 && <span>&middot; {member.volunteer_hours}h</span>}
          </div>
          {badges.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {badges.slice(0, 3).map((b) => (
                <span key={b} className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-100">{b}</span>
              ))}
              {badges.length > 3 && <span className="text-[9px] text-slate-400">+{badges.length - 3}</span>}
            </div>
          )}
        </div>
      </div>
      <Button size="sm" variant="outline" onClick={() => onConnect(member)} className="shrink-0 rounded-full gap-1 text-xs border-[#28A9E2]/30 text-[#1E56A0] hover:bg-[#28A9E2]/5" data-testid={`connect-${member.email}`}>
        <MessageCircle className="w-3 h-3" /> {t.connect}
      </Button>
    </div>
  );
}

function ThreadView({ otherUser, currentEmail, onBack, t }) {
  const [messages, setMessages] = useState([]);
  const [newMsg, setNewMsg] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef(null);

  const fetchThread = useCallback(async () => {
    try {
      const { data } = await api.get(`/messages/thread/${otherUser.email}`);
      setMessages(data);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setLoading(false); }
  }, [otherUser.email]);

  useEffect(() => { fetchThread(); const iv = setInterval(fetchThread, 5000); return () => clearInterval(iv); }, [fetchThread]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMsg.trim()) return;
    setSending(true);
    try {
      await api.post("/messages", { recipient_email: otherUser.email, message: newMsg.trim() });
      setNewMsg("");
      fetchThread();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSending(false); }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]" data-testid="thread-view">
      <div className="flex items-center gap-3 pb-4 border-b border-sky-100">
        <button onClick={onBack} className="p-1.5 rounded-lg hover:bg-sky-50 text-slate-400 hover:text-[#1E56A0] transition-colors" data-testid="thread-back-btn">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="w-9 h-9 rounded-full bg-[#1E56A0]/10 flex items-center justify-center text-[#1E56A0] font-semibold text-sm">
          {otherUser.name?.charAt(0)?.toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-medium text-[#0D2847]">{otherUser.name}</p>
          <p className="text-xs text-slate-400">{otherUser.email}</p>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-2.5 mt-3 flex gap-2 items-start">
        <ShieldAlert className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
        <p className="text-[10px] text-amber-700">{t.security_notice}</p>
      </div>

      <div className="flex-1 overflow-y-auto py-4 space-y-3 min-h-0">
        {loading ? <p className="text-center text-slate-400 text-sm py-8">{t.loading}</p> :
         messages.length === 0 ? <p className="text-center text-slate-400 text-sm py-8">{t.no_messages}</p> :
         messages.map((m) => {
           const isMine = m.sender_email === currentEmail;
           return (
             <div key={m.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
               <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${isMine ? "bg-[#1E56A0] text-white rounded-br-md" : "bg-white border border-sky-100 text-[#0D2847] rounded-bl-md"}`} data-testid={`msg-${m.id}`}>
                 <p className="text-sm whitespace-pre-wrap break-words">{m.message}</p>
                 <p className={`text-[10px] mt-1 ${isMine ? "text-blue-200" : "text-slate-400"}`}>
                   {new Date(m.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
                 </p>
               </div>
             </div>
           );
         })
        }
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-2 pt-3 border-t border-sky-100">
        <Input value={newMsg} onChange={(e) => setNewMsg(e.target.value)} placeholder={t.type_message} className="flex-1 rounded-xl" data-testid="message-input" />
        <Button type="submit" disabled={sending || !newMsg.trim()} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-xl px-4" data-testid="send-message-btn">
          <Send className="w-4 h-4" />
        </Button>
      </form>
    </div>
  );
}

export default function Community() {
  const { user, loading: authLoading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].community;
  const [members, setMembers] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [search, setSearch] = useState("");
  const [activeThread, setActiveThread] = useState(null);
  const [view, setView] = useState("directory");
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [memRes, convRes] = await Promise.all([
        api.get("/directory"),
        api.get("/messages/conversations"),
      ]);
      setMembers(memRes.data);
      setConversations(convRes.data);
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { if (user) fetchData(); }, [user, fetchData]);

  if (authLoading) return <div className="min-h-screen flex items-center justify-center text-slate-400">{t.loading}</div>;
  if (!user) return <Navigate to="/login" replace />;

  const filtered = members.filter((m) =>
    m.email !== user.email && m.name?.toLowerCase().includes(search.toLowerCase())
  );

  const handleConnect = (member) => {
    setActiveThread(member);
    setView("thread");
  };

  return (
    <div data-testid="community-page">
      <section className="relative py-16 sm:py-20 bg-[#1E56A0]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-4">
            <Users className="w-7 h-7 text-white" />
          </motion.div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.title}
          </h1>
          <p className="text-sm sm:text-base text-blue-100 mt-2">
            {t.subtitle}
          </p>
        </div>
      </section>

      <section className="py-8 sm:py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          {view === "thread" && activeThread ? (
            <ThreadView otherUser={activeThread} currentEmail={user.email} onBack={() => { setView("directory"); setActiveThread(null); fetchData(); }} t={t} />
          ) : (
            <>
              <div className="flex gap-1 bg-white/80 rounded-xl p-1 border border-sky-100 mb-6" data-testid="community-tabs">
                <button onClick={() => setView("directory")} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${view === "directory" ? "bg-[#1E56A0] text-white" : "text-slate-500 hover:text-[#1E56A0]"}`} data-testid="tab-directory">
                  {t.directory} ({filtered.length})
                </button>
                <button onClick={() => setView("conversations")} className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${view === "conversations" ? "bg-[#1E56A0] text-white" : "text-slate-500 hover:text-[#1E56A0]"}`} data-testid="tab-conversations">
                  {t.messages_tab} ({conversations.length})
                </button>
              </div>

              {view === "directory" && (
                <>
                  <div className="relative mb-4">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={t.search_placeholder} className="pl-10 rounded-xl" data-testid="directory-search" />
                  </div>
                  <div className="space-y-2">
                    {loading ? <p className="text-center text-slate-400 py-8">{t.loading}</p> :
                     filtered.length === 0 ? <p className="text-center text-slate-400 py-8">{t.no_members}</p> :
                     filtered.map((m) => <MemberCard key={m.email} member={m} onConnect={handleConnect} t={t} />)
                    }
                  </div>
                </>
              )}

              {view === "conversations" && (
                <div className="space-y-2" data-testid="conversations-list">
                  {conversations.length === 0 ? <p className="text-center text-slate-400 py-8">{t.no_conversations}</p> :
                   conversations.map((c) => (
                     <div key={c.email} onClick={() => handleConnect({ email: c.email, name: c.name })}
                       className="bg-white rounded-xl border border-sky-100 shadow-sm p-4 flex items-center justify-between cursor-pointer hover:shadow-md transition-shadow"
                       data-testid={`convo-${c.email}`}
                     >
                       <div className="flex items-center gap-3 min-w-0">
                         <div className="w-10 h-10 rounded-full bg-[#28A9E2]/10 flex items-center justify-center text-[#28A9E2] font-semibold text-sm">
                           {c.name?.charAt(0)?.toUpperCase() || "?"}
                         </div>
                         <div className="min-w-0">
                           <p className="text-sm font-medium text-[#0D2847]">{c.name}</p>
                           <p className="text-xs text-slate-400 truncate">{c.last_message_preview || "..."}</p>
                         </div>
                       </div>
                       <div className="flex items-center gap-2 shrink-0">
                         <span className="text-[10px] text-slate-400">{formatDate(c.last_time)}</span>
                         <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#1E56A0] text-white">{c.count}</span>
                       </div>
                     </div>
                   ))
                  }
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
