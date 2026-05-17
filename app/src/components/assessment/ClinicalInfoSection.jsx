import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { User } from "lucide-react";

export default function ClinicalInfoSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <User className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold tracking-tight">Patient Information</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="space-y-2">
          <Label htmlFor="patient_id" className="text-xs text-muted-foreground">Patient ID</Label>
          <Input
            id="patient_id"
            placeholder="e.g. PT-001"
            value={data.patient_id || ""}
            onChange={(e) => update("patient_id", e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="patient_age" className="text-xs text-muted-foreground">Age (years)</Label>
          <Input
            id="patient_age"
            type="number"
            placeholder="e.g. 28"
            value={data.patient_age || ""}
            onChange={(e) => update("patient_age", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="weight_kg" className="text-xs text-muted-foreground">Weight (kg)</Label>
          <Input
            id="weight_kg"
            type="number"
            step="0.1"
            placeholder="e.g. 65"
            value={data.weight_kg || ""}
            onChange={(e) => update("weight_kg", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="height_cm" className="text-xs text-muted-foreground">Height (cm)</Label>
          <Input
            id="height_cm"
            type="number"
            step="0.1"
            placeholder="e.g. 165"
            value={data.height_cm || ""}
            onChange={(e) => update("height_cm", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="bmi" className="text-xs text-muted-foreground">BMI (kg/m²)</Label>
          <Input
            id="bmi"
            type="text"
            placeholder="Auto-calculated"
            value={data.bmi || ""}
            disabled
          />
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Menstrual Regularity</Label>
          <Select value={data.menstrual_regularity || ""} onValueChange={(v) => update("menstrual_regularity", v)}>
            <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="regular">Regular</SelectItem>
              <SelectItem value="irregular">Irregular</SelectItem>
              <SelectItem value="absent">Absent (amenorrhea)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="cycle_length" className="text-xs text-muted-foreground">Cycle Length (days)</Label>
          <Input
            id="cycle_length"
            type="number"
            placeholder="e.g. 35"
            value={data.cycle_length || ""}
            onChange={(e) => update("cycle_length", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Recent Weight Gain</Label>
          <Select value={data.weight_gain || ""} onValueChange={(v) => update("weight_gain", v)}>
            <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="mild">Mild</SelectItem>
              <SelectItem value="moderate">Moderate</SelectItem>
              <SelectItem value="significant">Significant</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="waist_inch" className="text-xs text-muted-foreground">Waist circumference (inch)</Label>
          <Input
            id="waist_inch"
            type="number"
            step="0.1"
            placeholder="e.g. 32"
            value={data.waist_inch || ""}
            onChange={(e) => update("waist_inch", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="hip_inch" className="text-xs text-muted-foreground">Hip circumference (inch)</Label>
          <Input
            id="hip_inch"
            type="number"
            step="0.1"
            placeholder="e.g. 38"
            value={data.hip_inch || ""}
            onChange={(e) => update("hip_inch", parseFloat(e.target.value) || "")}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="waist_hip_ratio" className="text-xs text-muted-foreground">Waist:Hip Ratio</Label>
          <Input
            id="waist_hip_ratio"
            type="text"
            placeholder="Auto-calculated"
            value={data.waist_hip_ratio || ""}
            disabled
          />
        </div>
      </div>
    </div>
  );
}