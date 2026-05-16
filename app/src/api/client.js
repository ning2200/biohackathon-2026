const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY;
const OPENAI_MODEL = import.meta.env.VITE_OPENAI_MODEL || 'gpt-4o-mini';
const OPENAI_API_URL = import.meta.env.VITE_OPENAI_API_URL // || 'https://api.openai.com/v1/chat/completions';
const STORAGE_KEY = 'app_assessments';

const parseJsonResponse = (text) => {
  try {
    return JSON.parse(text);
  } catch (error) {
    // Try to extract JSON from text if the model includes extra content.
    const match = text.match(/\{[\s\S]*\}/);
    if (match) {
      return JSON.parse(match[0]);
    }
    throw error;
  }
};

const saveAssessments = (assessments) => {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(assessments));
};

const loadAssessments = () => {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw);
  } catch {
    return [];
  }
};

const createAssessment = async (payload) => {
  const current = loadAssessments();
  const assessment = {
    id: payload.patient_id ? `${payload.patient_id}-${Date.now()}` : `${Date.now()}`,
    created_date: new Date().toISOString(),
    ...payload,
  };
  const updated = [assessment, ...current];
  saveAssessments(updated);
  return assessment;
};

const listAssessments = async (sort = '-created_date', limit = 50) => {
  const current = loadAssessments();
  return current
    .sort((a, b) => new Date(b.created_date).getTime() - new Date(a.created_date).getTime())
    .slice(0, limit);
};

const invokeLLM = async ({ prompt, response_json_schema }) => {
  if (!OPENAI_API_KEY) {
    throw new Error('Missing VITE_OPENAI_API_KEY environment variable.');
  }

  const schemaText = response_json_schema
    ? `Respond only with valid JSON that matches this schema: ${JSON.stringify(response_json_schema)}`
    : '';

  const messages = [
    {
      role: 'system',
      content: 'You are a JSON-only response engine. Answer user prompts precisely and return only the requested JSON object.',
    },
    {
      role: 'user',
      content: `${prompt}\n\n${schemaText}`,
    },
  ];

  const response = await fetch(OPENAI_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: OPENAI_MODEL,
      messages,
      temperature: 0,
      max_tokens: 1000,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`OpenAI request failed: ${response.status} ${response.statusText} ${errorBody}`);
  }

  const json = await response.json();
  const assistant = json.choices?.[0]?.message?.content || json.choices?.[0]?.text;
  if (!assistant) {
    throw new Error('OpenAI response did not contain assistant content.');
  }

  return parseJsonResponse(assistant.trim());
};

export const openai = {
  integrations: {
    Core: {
      InvokeLLM: invokeLLM,
    },
  },
  entities: {
    Assessment: {
      create: createAssessment,
      list: listAssessments,
    },
  },
};