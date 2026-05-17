import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, Info, ArrowRight, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const riskConfig = {
  low: {
    color: "text-emerald-600",
    bg: "bg-emerald-50 border-emerald-200",
    badgeBg: "bg-emerald-100 text-emerald-700 border-emerald-300",
    icon: CheckCircle,
    label: "Low Risk",
  },
  moderate: {
    color: "text-amber-600",
    bg: "bg-amber-50 border-amber-200",
    badgeBg: "bg-amber-100 text-amber-700 border-amber-300",
    icon: AlertTriangle,
    label: "Moderate Risk",
  },
  high: {
    color: "text-red-600",
    bg: "bg-red-50 border-red-200",
    badgeBg: "bg-red-100 text-red-700 border-red-300",
    icon: ShieldAlert,
    label: "High Risk",
  },
};

export default function RiskResultCard({ result }) {
  const config = riskConfig[result.risk_level] || riskConfig.moderate;
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="space-y-6"
    >
      {/* Risk Level Banner */}
      <div className={`rounded-xl border-2 p-6 ${config.bg}`}>
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-xl flex items-center justify-center ${config.badgeBg}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">PMOS Risk Level</p>
            <h2 className={`text-2xl font-bold font-serif ${config.color}`}>{config.label}</h2>
          </div>
        </div>
      </div>

      {/* Top Reasons */}
      {result.top_reasons?.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Info className="h-4 w-4 text-primary" />
            Top Contributing Factors
          </h3>
          <div className="flex flex-wrap gap-2">
            {result.top_reasons.map((reason, i) => (
              <Badge key={i} variant="outline" className="px-3 py-1.5 text-xs font-medium bg-card">
                {reason}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <Separator />

      {/* Next Steps */}
      {result.next_steps?.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <ArrowRight className="h-4 w-4 text-accent" />
            Suggested Next Steps
          </h3>
          <ul className="space-y-2">
            {result.next_steps.map((step, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground">
                <span className="flex-shrink-0 h-5 w-5 rounded-full bg-accent/10 text-accent flex items-center justify-center text-[10px] font-bold mt-0.5">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ul>
        </div>
      )}

      <Separator />

      {/* Full Explanation */}
      {result.full_explanation && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">Clinical Reasoning</h3>
          <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
            {result.full_explanation}
          </p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="rounded-lg bg-secondary/60 border border-border p-4">
        <div className="flex gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-muted-foreground leading-relaxed">
            <strong className="text-foreground">Confidence Warning:</strong> This is not a diagnosis. This tool provides risk stratification only. Apply the Rotterdam criteria (≥2 of: oligo/anovulation, clinical/biochemical hyperandrogenism, polycystic ovarian morphology) and exclude other causes including thyroid disease, congenital adrenal hyperplasia, Cushing's syndrome, and hyperprolactinemia.
          </p>
        </div>
      </div>
    </motion.div>
  );
}