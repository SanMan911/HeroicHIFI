import { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { useLang } from "../context/LanguageContext";
import translations from "../data/translations";
import { Navigate } from "react-router-dom";
import api, { formatApiError } from "../lib/api";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { User, Award, Clock, IndianRupee, Camera, Save, Shield, Ticket } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";

const BADGE_COLORS = {
  "Helping Hero": "bg-green-100 text-green-800 border-green-200",
  "Century Hero": "bg-yellow-100 text-yellow-800 border-yellow-200",
  "Generous Soul": "bg-amber-100 text-amber-800 border-amber-200",
  "Community Builder": "bg-blue-100 text-blue-800 border-blue-200",
  "Star Volunteer of the Month": "bg-pink-100 text-pink-800 border-pink-200",
  "Star Volunteer of the Quarter": "bg-purple-100 text-purple-800 border-purple-200",
  "Star Volunteer of the Year": "bg-red-100 text-red-800 border-red-200",
  "Top Donor": "bg-orange-100 text-orange-800 border-orange-200",
  "Rising Star": "bg-cyan-100 text-cyan-800 border-cyan-200",
};

export default function Profile() {
  const { user, loading: authLoading } = useAuth();
  const { lang } = useLang();
  const t = translations[lang].profile;
  const [profile, setProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: "", phone: "", address: "" });
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [picUrl, setPicUrl] = useState(null);

  const fetchProfile = useCallback(async () => {
    try {
      const { data } = await api.get("/profile");
      setProfile(data);
      setForm({ name: data.name || "", phone: data.phone || "", address: data.address || "" });
      if (data.profile_pic_path) {
        loadPic(data.profile_pic_path);
      }
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    }
  }, []);

  const loadPic = async (path) => {
    try {
      const token = localStorage.getItem("hhf_token");
      const resp = await api.get(`/files/${path}`, { responseType: "blob", headers: { Authorization: `Bearer ${token}` } });
      setPicUrl(URL.createObjectURL(resp.data));
    } catch {
      setPicUrl(null);
    }
  };

  useEffect(() => { if (user) fetchProfile(); }, [user, fetchProfile]);

  if (authLoading) return null;
  if (!user) return <Navigate to="/login" replace />;

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/profile/upload-pic", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(t.pic_uploaded);
      if (data.path) loadPic(data.path);
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setUploading(false); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/profile", form);
      toast.success(t.profile_updated);
      setEditing(false);
      fetchProfile();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setSaving(false); }
  };

  return (
    <div data-testid="profile-page">
      <section className="relative py-16 sm:py-20 bg-[#1E56A0]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-white" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
            {t.title}
          </h1>
        </div>
      </section>

      <section className="py-8 sm:py-12">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          {!profile ? (
            <p className="text-center text-slate-400 py-12">{t.loading}</p>
          ) : (
            <div className="space-y-6">
              {/* Avatar + Name */}
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 flex flex-col sm:flex-row items-center gap-6">
                <div className="relative group">
                  <div className="w-24 h-24 rounded-full bg-[#1E56A0]/10 flex items-center justify-center overflow-hidden border-4 border-sky-100">
                    {picUrl ? (
                      <img src={picUrl} alt="Profile" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-10 h-10 text-[#1E56A0]" />
                    )}
                  </div>
                  <label className="absolute inset-0 flex items-center justify-center bg-black/30 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity" data-testid="upload-pic-label">
                    <Camera className="w-6 h-6 text-white" />
                    <input type="file" accept="image/*" className="hidden" onChange={handleUpload} disabled={uploading} data-testid="upload-pic-input" />
                  </label>
                </div>
                <div className="text-center sm:text-left flex-1">
                  <h2 className="text-2xl font-semibold text-[#0D2847]" style={{ fontFamily: "'Cormorant Garamond', serif" }}>{profile.name}</h2>
                  <p className="text-sm text-slate-500">{profile.email}</p>
                  <p className="text-xs text-[#1E56A0] font-medium mt-1">{profile.role === "admin" ? t.admin : t.volunteer}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => setEditing(!editing)} className="rounded-full gap-1" data-testid="edit-profile-btn">
                  <Save className="w-3 h-3" /> {editing ? t.cancel : t.edit}
                </Button>
              </motion.div>

              {/* Edit Form */}
              {editing && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 space-y-4">
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.name}</Label>
                    <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-name" />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.phone}</Label>
                    <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-phone" />
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-slate-700">{t.address}</Label>
                    <Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="mt-1 rounded-xl" data-testid="edit-address" />
                  </div>
                  <Button onClick={handleSave} disabled={saving} className="bg-[#1E56A0] hover:bg-[#174A8A] text-white rounded-full px-6" data-testid="save-profile-btn">
                    {saving ? "..." : t.save}
                  </Button>
                </motion.div>
              )}

              {/* Stats Row */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <Clock className="w-5 h-5 text-[#1E56A0] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{profile.volunteer_hours}</p>
                  <p className="text-xs text-slate-500">{t.hours}</p>
                </div>
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <IndianRupee className="w-5 h-5 text-[#FF7F00] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{(profile.total_donated || 0).toLocaleString("en-IN")}</p>
                  <p className="text-xs text-slate-500">{t.total_donated}</p>
                </div>
                <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-4 text-center">
                  <Award className="w-5 h-5 text-[#16A34A] mx-auto mb-2" />
                  <p className="text-2xl font-bold text-[#0D2847]">{(profile.badges || []).length}</p>
                  <p className="text-xs text-slate-500">{t.badges_count}</p>
                </div>
              </div>

              {/* Badges */}
              <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6">
                <h3 className="text-lg font-medium text-[#0D2847] mb-4 flex items-center gap-2" style={{ fontFamily: "'Cormorant Garamond', serif" }}>
                  <Award className="w-5 h-5 text-[#FF7F00]" /> {t.badges_title}
                </h3>
                <div className="flex flex-wrap gap-2" data-testid="badges-list">
                  {(profile.badges || []).map((b) => (
                    <span key={b} className={`text-xs px-3 py-1.5 rounded-full border font-medium ${BADGE_COLORS[b] || "bg-slate-100 text-slate-700 border-slate-200"}`} data-testid={`badge-${b.replace(/\s/g, "-")}`}>
                      {b}
                    </span>
                  ))}
                  {(profile.badges || []).length === 0 && <p className="text-sm text-slate-400">{t.no_badges}</p>}
                </div>
              </div>

              {/* Quick Links */}
              <div className="flex flex-wrap gap-3">
                <Link to="/tickets">
                  <Button variant="outline" className="rounded-full gap-2 text-sm border-sky-200" data-testid="go-to-tickets">
                    <Ticket className="w-4 h-4" /> {t.my_tickets}
                  </Button>
                </Link>
                <Link to="/community">
                  <Button variant="outline" className="rounded-full gap-2 text-sm border-sky-200" data-testid="go-to-community">
                    <Shield className="w-4 h-4" /> {t.community_link}
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
