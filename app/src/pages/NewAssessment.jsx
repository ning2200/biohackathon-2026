import { useState } from "react";
import { openai } from "@/api/client.js";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Loader2, Send, RotateCcw } from "lucide-react";
import ClinicalInfoSection from "@/components/assessment/ClinicalInfoSection";
import SymptomsSection from "@/components/assessment/SymptomsSection";
import LabResultsSection from "@/components/assessment/LabResultsSection";
import RiskResultCard from "@/components/assessment/RiskResultCard";

// baseline: weight, height, pulse rate, respiratory rate, hemoglobin -> calculate bmi
// reproductive, cycle history: cycle pattern, cycle length, progesterone, fsh, lh, endometrium thickness
// endocrine, metabolic markers: tsh, amh, prolactin, witamin d3, random blood sugar, systolic blood pressure
// , diastolic blood pressure, waist circumference, hip circumference
// symptoms, lifestyle: recent weight gain, hair growth/hirsutism, skin darkening, hair loss, pimples/acne
// , frequent fast food intake, regular exercise
const initialData = {
  patient_id: "",
  patient_age: "",
  weight_kg: "",
  height_cm: "",
  menstrual_regularity: "",
  cycle_length: "",
  bmi: "",
  weight_gain: "",
  hirsutism: "",
  acne: "",
  skin_darkening: false,
  hair_loss: "",
  regular_exercise: "",
  fast_food: "",
  amh: "",
  lh: "",
  fsh: "",
  fsh_lh: "",
  follicle_count_left: "",
  follicle_count_right: "",
  waist_inch: "",
  hip_inch: "",
  waist_hip_ratio: "",
  fasting_glucose: "",
  systolic_bp: "",
  diastolic_bp: "",
};

const computeDerivedValues = (payload) => {
  const next = { ...payload };

  const weight = parseFloat(next.weight_kg);
  const height = parseFloat(next.height_cm);
  next.bmi = Number.isFinite(weight) && Number.isFinite(height) && height > 0
    ? Number((weight / ((height / 100) ** 2)).toFixed(1))
    : "";

  const fsh = parseFloat(next.fsh);
  const lh = parseFloat(next.lh);
  next.fsh_lh = Number.isFinite(fsh) && Number.isFinite(lh) && lh > 0
    ? Number((fsh / lh).toFixed(2))
    : "";

  const waist = parseFloat(next.waist_inch);
  const hip = parseFloat(next.hip_inch);
  next.waist_hip_ratio = Number.isFinite(waist) && Number.isFinite(hip) && hip > 0
    ? Number((waist / hip).toFixed(3))
    : "";

  return next;
};

export default function NewAssessment() {
  const [formData, setFormData] = useState(initialData);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFormChange = (updates) => {
    setFormData((current) => computeDerivedValues({ ...current, ...updates }));
  };

  const handleSubmit = async () => {
    if (!formData.patient_id) return;
    setLoading(true);
    setResult(null);

    const response = await openai.entities.Assessment.submit(formData);
    setResult(response);

    // Save assessment locally as well.
    await openai.entities.Assessment.create({
      ...formData,
      ...response,
    });

    setLoading(false);
  };

  const handleReset = () => {
    setFormData(initialData);
    setResult(null);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold font-serif tracking-tight">New Risk Assessment</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Enter patient clinical data to generate an explainable PMOS risk triage.
        </p>
      </div>

      {/* Form */}
      <Card className="shadow-sm">
        <CardContent className="p-6 space-y-8">
          <ClinicalInfoSection data={formData} onChange={handleFormChange} />
          <Separator />
          <SymptomsSection data={formData} onChange={handleFormChange} />
          <Separator />
          <LabResultsSection data={formData} onChange={handleFormChange} />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          onClick={handleSubmit}
          disabled={loading || !formData.patient_id}
          className="flex-1 sm:flex-none sm:min-w-[200px]"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Run Assessment
            </>
          )}
        </Button>
        <Button variant="outline" onClick={handleReset} size="lg">
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset
        </Button>
      </div>

      {/* Results */}
      {result && <RiskResultCard result={result} />}
    </div>
  );
}