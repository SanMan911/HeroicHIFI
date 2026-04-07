import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useLang } from "../context/LanguageContext";
import api from "../lib/api";
import { MEDIA } from "../data/missions";
import { Button } from "../components/ui/button";
import { motion } from "framer-motion";
import { ArrowLeft, Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt } from "lucide-react";

const iconMap = { Sparkles, Heart, BookOpen, UtensilsCrossed, TreePine, PawPrint, Shirt };

export default function MissionDetail() {
  const { slug } = useParams();
  const { lang } = useLang();
  const [mission, setMission] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/missions/${slug}`).then(({ data }) => {
      setMission(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-stone-400">Loading...</div>;
  if (!mission) return <div className="min-h-screen flex items-center justify-center text-stone-400">Mission not found</div>;

  const Icon = iconMap[mission.icon];
  const imageKey = mission.image_key;
  const image = MEDIA[imageKey] || MEDIA.hero_main;

  return (
    <div data-testid="mission-detail-page">
      <section className="relative min-h-[60vh] flex items-end overflow-hidden">
        <img src={image} alt={mission.name} className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 pb-16 w-full">
          <Link to="/missions" className="inline-flex items-center gap-2 text-white/70 hover:text-white mb-6 text-sm transition-colors" data-testid="back-to-missions">
            <ArrowLeft className="w-4 h-4" /> {lang === "hi" ? "सभी मिशन" : "All Missions"}
          </Link>
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full flex items-center justify-center" style={{ backgroundColor: mission.color }}>
              {Icon && <Icon className="w-6 h-6 text-white" />}
            </div>
          </div>
          <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-white mb-3"
            style={{ fontFamily: "'Cormorant Garamond', serif" }}
          >
            {lang === "hi" ? mission.name_hi : mission.name}
          </motion.h1>
          <p className="text-lg sm:text-xl text-stone-200">{lang === "hi" ? mission.tagline_hi : mission.tagline}</p>
        </div>
      </section>

      <section className="py-20 sm:py-28">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <motion.p initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            className="text-base sm:text-lg text-stone-600 leading-relaxed mb-10"
          >
            {lang === "hi" ? mission.description_hi : mission.description}
          </motion.p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link to="/donate">
              <Button className="bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-full px-8 py-3" data-testid="mission-donate-btn">
                {lang === "hi" ? "इस मिशन के लिए दान करें" : "Donate to This Mission"}
              </Button>
            </Link>
            <Link to="/volunteer">
              <Button variant="outline" className="border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A]/5 rounded-full px-8 py-3" data-testid="mission-volunteer-btn">
                {lang === "hi" ? "स्वयंसेवक बनें" : "Volunteer for This Mission"}
              </Button>
            </Link>
            <Link to={`/contact?mission=${slug}`}>
              <Button variant="outline" className="border-stone-300 text-stone-600 hover:bg-stone-50 rounded-full px-8 py-3" data-testid="mission-query-btn">
                {lang === "hi" ? "प्रश्न पूछें" : "Ask a Query"}
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
