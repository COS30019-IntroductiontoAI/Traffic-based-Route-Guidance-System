import { motion } from "framer-motion";
import { 
  Github, Mail, BookOpen, GraduationCap, Clock, UserCheck, 
  Code, Database, LayoutTemplate, Network 
} from "lucide-react";

// Animation config
const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] as const } },
};

// Team data
const teamMembers = [
  {
    name: "Do Gia Huy",
    id: "104988294",
    role: "Leader",
    tasks: "ML Implementation (LSTM/GRU), Model Evaluation, Data Processing & Dataset Preparation for 2014",
    icon: <UserCheck className="w-5 h-5 text-amber-500" />,
    borderColor: "border-amber-200",
    bgColor: "bg-amber-50",
    image: "/image/huy.jpg"
  },
  {
    name: "Bui Quang Doan",
    id: "104993227",
    role: "Member",
    tasks: "Data Processing & Dataset Preparation for 2006, Frontend Supporter",
    icon: <Database className="w-5 h-5 text-blue-500" />,
    borderColor: "border-blue-200",
    bgColor: "bg-blue-50",
    image: "/image/doan.jpg"
  },
  {
    name: "Huynh Doan Hoang Minh",
    id: "104777308",
    role: "Member",
    tasks: "ML Implementation (LightGBM), Model Evaluation, Backend, Frontend Supporter",
    icon: <Code className="w-5 h-5 text-emerald-500" />,
    borderColor: "border-emerald-200",
    bgColor: "bg-emerald-50",
    image: "/image/minh.jpg"
  },
  {
    name: "Le Thanh Nam",
    id: "104999380",
    role: "Member",
    tasks: "System Integration, Travel Time Estimation & GUI",
    icon: <LayoutTemplate className="w-5 h-5 text-purple-500" />,
    borderColor: "border-purple-200",
    bgColor: "bg-purple-50",
    image: "/image/nam.jpg"
  }
];

export default function AboutUs() {
  return (
    <div className="p-8 max-w-[1500px] w-full min-h-screen font-sans bg-gray-50/30">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
        
        {/* Header */}
        <motion.div variants={item} className="text-center max-w-2xl mx-auto mb-10">
          <h1 className="text-[32px] font-bold tracking-tight text-slate-800">
            Traffic-based Route Guidance System
          </h1>
          <p className="text-[16px] text-slate-500 font-medium mt-2">
            Assignment 2B_Machine Learning and Software Integration
          </p>
        </motion.div>

        {/* Project info */}
        <motion.div variants={item} className="bg-white rounded-[24px] border border-slate-200/60 p-8 shadow-sm max-w-5xl mx-auto flex flex-col md:flex-row gap-8 justify-between items-center relative overflow-hidden">
          
          {/* Background decoration */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full blur-3xl -z-10 opacity-60 translate-x-1/3 -translate-y-1/3"></div>

          <div className="space-y-5 flex-1">
            <h2 className="text-xl font-bold text-slate-800 border-b border-slate-100 pb-2">
              Unit Details
            </h2>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                  <BookOpen size={18} />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium uppercase">Unit</p>
                  <p className="text-sm font-semibold text-slate-700">
                    Introduction to AI (COS30019)
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-indigo-100 rounded-lg text-indigo-600">
                  <GraduationCap size={18} />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium uppercase">Lecturer</p>
                  <p className="text-sm font-semibold text-slate-700">
                    Dr. Quang Chiem
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-rose-100 rounded-lg text-rose-600">
                  <Clock size={18} />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium uppercase">Class Time</p>
                  <p className="text-sm font-semibold text-slate-700">
                    7:00 AM Saturday
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-emerald-100 rounded-lg text-emerald-600">
                  <Network size={18} />
                </div>
                <div>
                  <p className="text-xs text-slate-400 font-medium uppercase">Project Focus</p>
                  <p className="text-sm font-semibold text-slate-700">
                    ML & Route Optimization
                  </p>
                </div>
              </div>

            </div>
          </div>

          {/* GitHub link */}
          <div className="flex-shrink-0 flex flex-col items-center sm:items-end">
            <a 
              href="https://github.com/COS30019-IntroductiontoAI/Traffic-based-Route-Guidance-System.git" 
              target="_blank" 
              rel="noopener noreferrer"
              className="group flex items-center gap-3 bg-slate-900 hover:bg-slate-800 text-white px-6 py-4 rounded-2xl transition-all duration-300 shadow-md hover:shadow-xl hover:-translate-y-1"
            >
              <Github size={24} className="group-hover:scale-110 transition-transform" />
              <div className="text-left">
                <p className="text-xs font-medium text-slate-300">View Source Code</p>
                <p className="text-sm font-bold tracking-wide">GitHub Repository</p>
              </div>
            </a>
          </div>

        </motion.div>

        {/* Team section */}
        <div className="max-w-7xl mx-auto pt-4">
          <motion.h2 variants={item} className="text-2xl font-bold text-slate-800 text-center mb-8">
            Meet The Team
          </motion.h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {teamMembers.map((member, index) => (
              <motion.div 
                key={index} 
                variants={item}
                className="bg-white rounded-[24px] border border-slate-200/60 p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden flex flex-col h-full"
              >
                
                {/* Top strip */}
                <div className={`absolute top-0 left-0 right-0 h-1.5 ${member.bgColor}`}></div>
                
                <div className="flex flex-col items-center text-center mt-2 mb-4">
                  
                  {/* Avatar */}
                  <div className={`w-20 h-20 rounded-full border-4 ${member.borderColor} mb-4 overflow-hidden shadow-sm`}>
                    <img 
                      src={member.image} 
                      alt={member.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(member.name)}&background=random&color=fff&size=150`;
                      }}
                    />
                  </div>
                  
                  <h3 className="text-lg font-bold text-slate-800">{member.name}</h3>
                  <span className="text-[13px] font-semibold text-slate-500 mt-1">
                    ID: {member.id}
                  </span>
                  
                  <span className={`mt-2 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                    member.role === "Leader"
                      ? "bg-amber-100 text-amber-700"
                      : "bg-slate-100 text-slate-600"
                  }`}>
                    {member.role === "Leader" ? "★ Leader" : "Team Member"}
                  </span>
                </div>

                {/* Email */}
                <div className="flex items-center justify-center gap-2 py-3 border-t border-b border-slate-100 mb-4 bg-slate-50/50 -mx-6 px-6">
                  <Mail size={14} className="text-slate-400" />
                  <a href={`mailto:${member.id}@student.swin.edu.au`} className="text-[13px] font-medium text-blue-600 hover:underline">
                    {member.id}@student.swin.edu.au
                  </a>
                </div>

                {/* Tasks */}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {member.icon}
                    <h4 className="text-[13px] font-bold text-slate-700 uppercase">
                      Responsibilities
                    </h4>
                  </div>
                  <p className="text-[13px] text-slate-600 leading-relaxed font-medium">
                    {member.tasks}
                  </p>
                </div>

              </motion.div>
            ))}
          </div>
        </div>

      </motion.div>
    </div>
  );
}