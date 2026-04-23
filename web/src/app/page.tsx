"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { askQuestion, AskResponse, DemoCase, fetchDemoCases } from "@/lib/api";

const DEMO_FALLBACK: DemoCase[] = [
  {
    case_id: "transparence",
    title: "Obligations de transparence",
    question: "Quelles obligations de transparence pour les systemes IA ?",
    expected_refusal: false,
  },
  {
    case_id: "sanctions",
    title: "Sanctions en cas de violation",
    question: "Quelles sanctions sont prevues en cas de violation ?",
    expected_refusal: false,
  },
  {
    case_id: "definition",
    title: "Definition d'un systeme IA",
    question: "Comment le reglement definit un systeme IA ?",
    expected_refusal: false,
  },
  {
    case_id: "hors_perimetre",
    title: "Question hors perimetre",
    question: "Quel est le regime fiscal IA mondial detaille par pays ?",
    expected_refusal: true,
  },
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [demoCases, setDemoCases] = useState<DemoCase[]>([]);
  const [isLoadingCases, setIsLoadingCases] = useState(true);
  const [isAsking, setIsAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadCases() {
      try {
        const cases = await fetchDemoCases();
        if (mounted) {
          setDemoCases(cases);
        }
      } catch {
        if (mounted) {
          setDemoCases(DEMO_FALLBACK);
          setErrorMessage(
            "Impossible de charger les cas de demo depuis l'API. Affichage d'un jeu local de secours.",
          );
        }
      } finally {
        if (mounted) {
          setIsLoadingCases(false);
        }
      }
    }
    loadCases();
    return () => {
      mounted = false;
    };
  }, []);

  const canSubmit = useMemo(
    () => !isAsking && question.trim().length > 0,
    [isAsking, question],
  );

  async function onAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsAsking(true);
    try {
      const response = await askQuestion(question);
      setResult(response);
    } catch (error) {
      setResult(null);
      setErrorMessage(
        error instanceof Error
          ? `Erreur API: ${error.message}`
          : "Erreur API inconnue.",
      );
    } finally {
      setIsAsking(false);
    }
  }

  function applyDemoCase(value: string) {
    setQuestion(value);
    setErrorMessage("");
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl px-6 py-8 md:px-8 md:py-10">
      <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <p className="mb-2 text-xs font-medium uppercase tracking-wide text-indigo-600">
          AI Act RAG Assistant
        </p>
        <h1 className="text-2xl font-semibold text-zinc-900 md:text-3xl">
          Assistant documentaire AI Act
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600 md:text-base">
          Posez une question et obtenez une reponse structuree, sourcée et bornée
          au corpus charge. Le systeme indique explicitement ses limites quand la
          base documentaire est insuffisante.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-zinc-900">Question</h2>
        <form className="space-y-4" onSubmit={onAsk}>
          <textarea
            className="h-28 w-full resize-y rounded-xl border border-zinc-300 px-4 py-3 text-sm text-zinc-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            placeholder="Ex: Quelles obligations de transparence pour les systemes IA ?"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={!canSubmit}
            >
              {isAsking ? "Analyse en cours..." : "Lancer l'analyse"}
            </button>
            <span className="text-xs text-zinc-500">
              Le resultat s&apos;affiche sans rechargement de page.
            </span>
          </div>
        </form>
      </section>

      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-zinc-900">Cas de demo</h2>
        {isLoadingCases ? (
          <p className="text-sm text-zinc-500">Chargement des cas...</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {demoCases.map((item) => (
              <button
                key={item.case_id}
                type="button"
                onClick={() => applyDemoCase(item.question)}
                className="rounded-xl border border-zinc-200 px-4 py-3 text-left transition hover:border-indigo-300 hover:bg-indigo-50"
              >
                <p className="text-sm font-medium text-zinc-900">{item.title}</p>
                <p className="mt-1 text-xs text-zinc-500">{item.question}</p>
              </button>
            ))}
          </div>
        )}
      </section>

      {errorMessage ? (
        <section className="mt-6 rounded-2xl border border-amber-300 bg-amber-50 px-5 py-4 text-sm text-amber-900">
          {errorMessage}
        </section>
      ) : null}

      {result ? (
        <section className="mt-8 rounded-2xl border border-zinc-200 bg-white p-7 shadow-sm md:p-8">
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-zinc-100 px-3 py-1 font-medium text-zinc-700">
              retrieval: {result.retrieval_status}
            </span>
            {result.refusal ? (
              <span className="rounded-full bg-rose-100 px-3 py-1 font-medium text-rose-700">
                refus explicite
              </span>
            ) : (
              <span className="rounded-full bg-emerald-100 px-3 py-1 font-medium text-emerald-700">
                reponse sourcée
              </span>
            )}
            <span className="rounded-full bg-indigo-50 px-3 py-1 font-medium text-indigo-700">
              cas metier: {result.business_case}
            </span>
          </div>
          <p className="mb-6 whitespace-pre-wrap text-sm text-zinc-600">
            {result.retrieval_message}
          </p>

          <div className="space-y-6 md:space-y-7">
            <ResultBlock title="Reponse simple" items={[result.answer_simple]} />
            <ResultBlock
              title="Ce que cela veut dire pour votre entreprise"
              items={result.business_impact}
            />
            <ResultBlock title="Ce qu'il faut verifier" items={result.checks} />
            <ResultBlock title="Ce qui reste incertain" items={result.uncertainties} />
            <ResultBlock title="Sources" items={result.sources} />
            <ResultBlock title="Limites" items={result.limits} />
          </div>
        </section>
      ) : null}
    </main>
  );
}

function ResultBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 border-b border-zinc-100 pb-2 text-base font-semibold text-zinc-900">
        {title}
      </h3>
      {items.length > 0 ? (
        <ul className="space-y-4">
          {items.map((item, index) => (
            <li
              key={`${title}-${index}`}
              className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm leading-7 text-zinc-700"
            >
              <div className="space-y-2">
                {item.split("\n").map((line, lineIdx) => (
                  <p key={`${title}-${index}-${lineIdx}`} className="whitespace-pre-wrap">
                    {line}
                  </p>
                ))}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-zinc-500">Aucun element disponible.</p>
      )}
    </section>
  );
}
