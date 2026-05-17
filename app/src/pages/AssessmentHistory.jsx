import { openai } from "@/api/client.js";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, CheckCircle, ShieldAlert, ChevronRight } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import RiskResultCard from "@/components/assessment/RiskResultCard";

const riskIcons = {
  low: CheckCircle,
  moderate: AlertTriangle,
  high: ShieldAlert,
};

const riskBadgeStyles = {
  low: "bg-emerald-100 text-emerald-700 border-emerald-300",
  moderate: "bg-amber-100 text-amber-700 border-amber-300",
  high: "bg-red-100 text-red-700 border-red-300",
};

export default function AssessmentHistory() {
  const [expandedId, setExpandedId] = useState(null);

  const { data: assessments, isLoading } = useQuery({
    queryKey: ["assessments"],
    queryFn: () => openai.entities.Assessment.list("-created_date", 50),
    initialData: [],
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold font-serif tracking-tight">Assessment History</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Review past PMOS risk assessments and their outcomes.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array(4).fill(0).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-6 w-20 rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : assessments.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">No assessments yet. Run your first assessment to see results here.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {assessments.map((a) => {
            const Icon = riskIcons[a.risk_level] || AlertTriangle;
            const isExpanded = expandedId === a.id;

            return (
              <Card
                key={a.id}
                className="cursor-pointer transition-shadow hover:shadow-md"
                onClick={() => setExpandedId(isExpanded ? null : a.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${riskBadgeStyles[a.risk_level] || "bg-muted"}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{a.patient_id}</p>
                      <p className="text-xs text-muted-foreground">
                        {a.created_date ? format(new Date(a.created_date), "MMM d, yyyy 'at' h:mm a") : "—"}
                        {a.patient_age ? ` · Age ${a.patient_age}` : ""}
                      </p>
                    </div>
                    <Badge variant="outline" className={`${riskBadgeStyles[a.risk_level] || ""} border`}>
                      {a.risk_level ? a.risk_level.charAt(0).toUpperCase() + a.risk_level.slice(1) : "—"}
                    </Badge>
                    <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${isExpanded ? "rotate-90" : ""}`} />
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <div className="pt-5 mt-4 border-t border-border">
                          <RiskResultCard result={a} />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}