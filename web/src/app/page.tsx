"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { askQuestion, AskResponse, DemoCase, fetchDemoCases } from "@/lib/api";

// Lien de prise de RDV Inseil (reel, recupere depuis inseil.fr/inseil-ia/).
const CONTACT_URL = "https://calendly.com/inseil/45min";
const CONTACT_LABEL = "Reservez votre diagnostic IA offert";
const CONTACT_LABEL_SHORT = "Diagnostic IA offert";

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

const AUDIENCES: { role: string; benefit: string }[] = [
  {
    role: "Dirigeant TPE / PME",
    benefit:
      "Comprendre rapidement votre exposition au règlement et les actions à anticiper, sans jargon juridique",
  },
  {
    role: "Direction conformité",
    benefit:
      "Cadrer un sujet AI Act en quelques minutes avant de mobiliser un cabinet spécialisé",
  },
  {
    role: "RH / Recrutement",
    benefit:
      "Vérifier la transparence due aux candidats lors de l'usage d'outils IA",
  },
  {
    role: "Service client",
    benefit:
      "Cadrer l'usage des chatbots et l'information à donner aux utilisateurs",
  },
];

export default function Home() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [demoCases, setDemoCases] = useState<DemoCase[]>([]);
  const [isLoadingCases, setIsLoadingCases] = useState(true);
  const [isAsking, setIsAsking] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const questionSectionRef = useRef<HTMLElement | null>(null);

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
    questionSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function scrollToQuestion() {
    questionSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-5xl px-6 py-8 md:px-8 md:py-10">
      {/* Header marque */}
      <header className="mb-6 flex items-center justify-between border-b border-zinc-200 pb-4">
        <div className="flex flex-col">
          <span className="text-base font-semibold tracking-tight text-zinc-900">
            INSEIL IA &amp; Data
          </span>
          <span className="text-xs text-zinc-500">Accompagnement IA des TPE/PME</span>
        </div>
        <a
          href={CONTACT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="hidden text-xs font-medium text-blue-700 hover:text-blue-900 md:inline-block"
        >
          {CONTACT_LABEL_SHORT} →
        </a>
      </header>

      {/* Hero commercial */}
      <section className="rounded-2xl border border-zinc-200 bg-gradient-to-br from-blue-50 via-white to-white p-6 shadow-sm md:p-8">
        <p className="mb-2 text-xs font-medium uppercase tracking-wider text-blue-700">
          AI Act — Assistant documentaire
        </p>
        <h1 className="text-3xl font-semibold leading-tight text-zinc-900 md:text-4xl">
          Anticiper l&apos;AI Act européen.
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-zinc-700 md:text-base">
          Le Règlement européen 2024/1689 entre progressivement en application.
          Pour les dirigeants de TPE/PME, c&apos;est un sujet à clarifier vite,
          sans devoir lire 144 pages de texte juridique. Cet assistant vous
          permet d&apos;explorer le règlement officiel — articles, obligations,
          sanctions — avec des réponses sourcées et l&apos;honnêteté de dire
          « je ne sais pas » quand le règlement ne couvre pas votre cas.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={scrollToQuestion}
            className="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-800"
          >
            ▶ Tester maintenant
          </button>
          <a
            href={CONTACT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl border border-blue-200 bg-white px-5 py-2.5 text-sm font-medium text-blue-700 transition hover:border-blue-300 hover:bg-blue-50"
          >
            {CONTACT_LABEL} →
          </a>
        </div>
        <p className="mt-5 text-xs font-medium uppercase tracking-wide text-zinc-500">
          144 pages indexées · Citations vérifiables · Refus explicites
        </p>
      </section>

      {/* Pour qui c'est utile */}
      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900">
          Pour qui cet outil est utile
        </h2>
        <ul className="grid gap-3 md:grid-cols-2">
          {AUDIENCES.map((aud) => (
            <li
              key={aud.role}
              className="rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-3"
            >
              <p className="text-sm font-medium text-zinc-900">{aud.role}</p>
              <p className="mt-1 text-xs leading-5 text-zinc-600">{aud.benefit}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Cadre d'usage / disclaimer */}
      <section className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm leading-6 text-amber-900 md:px-6">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-amber-800">
          ⚠ Cadre d&apos;usage
        </p>
        <p>
          Cet outil est un assistant <strong>documentaire</strong>, il ne remplace
          pas un avis juridique. Pour toute décision de conformité, consultez un
          avocat ou un cabinet spécialisé. Corpus chargé : Règlement (UE) 2024/1689,
          Journal Officiel de l&apos;Union Européenne du 12 juillet 2024 (144 pages).
        </p>
      </section>

      {/* Question */}
      <section
        ref={questionSectionRef}
        className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
      >
        <h2 className="mb-3 text-lg font-semibold text-zinc-900">Posez votre question</h2>
        <form className="space-y-4" onSubmit={onAsk}>
          <textarea
            className="h-28 w-full resize-y rounded-xl border border-zinc-300 px-4 py-3 text-sm text-zinc-900 outline-none transition focus:border-blue-600 focus:ring-2 focus:ring-blue-100"
            placeholder="Ex : Quelles obligations de transparence pour les systemes IA ?"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="rounded-xl bg-blue-700 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={!canSubmit}
            >
              {isAsking ? "Analyse en cours..." : "Lancer l'analyse"}
            </button>
            <span className="text-xs text-zinc-500">
              Le résultat s&apos;affiche sans rechargement de page.
            </span>
          </div>
        </form>
      </section>

      {/* Cas de demo */}
      <section className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
        <h2 className="mb-3 text-lg font-semibold text-zinc-900">
          Suggestions de questions
        </h2>
        <p className="mb-4 text-xs text-zinc-500">
          Cliquez sur un exemple pour le pré-remplir, vous pouvez aussi poser
          librement vos propres questions.
        </p>
        {isLoadingCases ? (
          <p className="text-sm text-zinc-500">Chargement des cas...</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            {demoCases.map((item) => (
              <button
                key={item.case_id}
                type="button"
                onClick={() => applyDemoCase(item.question)}
                className="rounded-xl border border-zinc-200 px-4 py-3 text-left transition hover:border-blue-300 hover:bg-blue-50"
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
            <span className="rounded-full bg-blue-50 px-3 py-1 font-medium text-blue-700">
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

      {/* CTA bas de page */}
      <section className="mt-10 rounded-2xl border border-blue-200 bg-blue-50 p-6 text-center shadow-sm md:p-8">
        <h2 className="text-xl font-semibold text-zinc-900 md:text-2xl">
          Vous avez un sujet AI Act concret pour votre TPE/PME ?
        </h2>
        <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-zinc-700 md:text-base">
          Cet assistant donne un cadrage documentaire. Pour structurer votre
          conformité, qualifier vos systèmes ou préparer une revue interne,
          parlons-en directement. 45 minutes, sans engagement.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <a
            href={CONTACT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-xl bg-blue-700 px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-blue-800"
          >
            {CONTACT_LABEL} →
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-10 border-t border-zinc-200 pt-6 pb-4 text-xs text-zinc-500">
        <div className="flex flex-col items-start justify-between gap-2 md:flex-row md:items-center">
          <span>
            <strong className="font-semibold text-zinc-700">INSEIL IA &amp; Data</strong> ·
            Accompagnement IA des TPE/PME ·{" "}
            <a
              href="https://inseil.fr"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 hover:underline"
            >
              inseil.fr
            </a>
          </span>
          <span>
            Démo documentaire — pas un avis juridique. Source : JOUE 12/07/2024.
          </span>
        </div>
      </footer>
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
