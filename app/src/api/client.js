function assertResponse(response) {
  if (!response.ok) {
    return response.text().then((text) => {
      throw new Error(`API request failed ${response.status}: ${text}`);
    });
  }
  return response.json();
}

const storageKey = "pmos_assessments";

function saveAssessmentLocally(assessment) {
  const existing = JSON.parse(window.localStorage.getItem(storageKey) || "[]");
  const record = {
    id: assessment.patient_id || `local-${Date.now()}`,
    created_date: new Date().toISOString(),
    ...assessment,
  };
  const updated = [record, ...existing].slice(0, 100);
  window.localStorage.setItem(storageKey, JSON.stringify(updated));
  return record;
}

export const openai = {
  entities: {
    Assessment: {
      submit: async (data) => {
        const response = await fetch("/api/assessments", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });
        return assertResponse(response);
      },
      create: async (assessment) => {
        return saveAssessmentLocally(assessment);
      },
      list: async (_sortKey = "-created_date", limit = 50) => {
        const existing = JSON.parse(window.localStorage.getItem(storageKey) || "[]");
        return existing
          .slice()
          .sort((a, b) => new Date(b.created_date) - new Date(a.created_date))
          .slice(0, limit);
      },
    },
  },
};
