import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FlaskConical } from "lucide-react";

export default function LabResultsSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });

  const fields = [
    { id: "amh", label: "AMH (ng/mL)", placeholder: "e.g. 5.2" },
    { id: "lh", label: "LH (IU/L)", placeholder: "e.g. 12.5" },
    { id: "fsh", label: "FSH (IU/L)", placeholder: "e.g. 5.8" },
    { id: "follicle_count_left", label: "Follicle Count – Left Ovary", placeholder: "e.g. 14" },
    { id: "follicle_count_right", label: "Follicle Count – Right Ovary", placeholder: "e.g. 16" },
    { id: "fasting_glucose", label: "Fasting Glucose (mg/dL)", placeholder: "e.g. 98" },
    { id: "systolic_bp", label: "Systolic BP (mmHg)", placeholder: "e.g. 125" },
    { id: "diastolic_bp", label: "Diastolic BP (mmHg)", placeholder: "e.g. 82" },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <FlaskConical className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold tracking-tight">Lab & Imaging Results</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {fields.map((f) => (
          <div key={f.id} className="space-y-2">
            <Label htmlFor={f.id} className="text-xs text-muted-foreground">{f.label}</Label>
            <Input
              id={f.id}
              type="number"
              step="0.1"
              placeholder={f.placeholder}
              value={data[f.id] || ""}
              onChange={(e) => update(f.id, parseFloat(e.target.value) || "")}
            />
          </div>
        ))}
        <div className="space-y-2">
          <Label htmlFor="fsh_lh" className="text-xs text-muted-foreground">FSH/LH Ratio</Label>
          <Input
            id="fsh_lh"
            type="text"
            placeholder="Auto-calculated"
            value={data.fsh_lh || ""}
            disabled
          />
        </div>
      </div>
      {data.lh && data.fsh && data.fsh > 0 && (
        <div className="rounded-lg bg-secondary/60 px-4 py-3">
          <p className="text-xs text-muted-foreground">
            Computed LH/FSH Ratio:{" "}
            <span className="font-semibold text-foreground">
              {(data.lh / data.fsh).toFixed(2)}
            </span>
          </p>
        </div>
      )}
    </div>
  );
}