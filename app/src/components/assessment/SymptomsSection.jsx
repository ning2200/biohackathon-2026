import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Stethoscope } from "lucide-react";

const severityOptions = [
  { value: "none", label: "None" },
  { value: "mild", label: "Mild" },
  { value: "moderate", label: "Moderate" },
  { value: "severe", label: "Severe" },
];

export default function SymptomsSection({ data, onChange }) {
  const update = (field, value) => onChange({ ...data, [field]: value });

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <Stethoscope className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold tracking-tight">Clinical Symptoms</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Hirsutism (excess hair growth)</Label>
          <Select value={data.hirsutism || ""} onValueChange={(v) => update("hirsutism", v)}>
            <SelectTrigger><SelectValue placeholder="Select severity" /></SelectTrigger>
            <SelectContent>
              {severityOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Acne / Pimples</Label>
          <Select value={data.acne || ""} onValueChange={(v) => update("acne", v)}>
            <SelectTrigger><SelectValue placeholder="Select severity" /></SelectTrigger>
            <SelectContent>
              {severityOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Hair Loss / Thinning</Label>
          <Select value={data.hair_loss || ""} onValueChange={(v) => update("hair_loss", v)}>
            <SelectTrigger><SelectValue placeholder="Select severity" /></SelectTrigger>
            <SelectContent>
              {severityOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Regular Exercise</Label>
          <Select value={data.regular_exercise || ""} onValueChange={(v) => update("regular_exercise", v)}>
            <SelectTrigger><SelectValue placeholder="Yes / No" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Frequent Fast Food Intake</Label>
          <Select value={data.fast_food || ""} onValueChange={(v) => update("fast_food", v)}>
            <SelectTrigger><SelectValue placeholder="Yes / No" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="yes">Yes</SelectItem>
              <SelectItem value="no">No</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center justify-between rounded-lg border border-border p-3">
          <div>
            <Label className="text-xs text-muted-foreground">Skin Darkening</Label>
            <p className="text-[11px] text-muted-foreground/70">Acanthosis nigricans</p>
          </div>
          <Switch
            checked={!!data.skin_darkening}
            onCheckedChange={(v) => update("skin_darkening", v)}
          />
        </div>
      </div>
    </div>
  );
}