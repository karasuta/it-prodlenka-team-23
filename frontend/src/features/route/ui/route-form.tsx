import { useState } from "react";

import { buildRoute } from "../api/build-route";
import type { RouteResponse } from "../model/route";
import { RouteList } from "./route-list";

const AUDIENCES = [
  "Новичок, ничего не понимаю в искусстве",
  "Родители с детьми",
  "Турист, пришёл впервые",
  "Студент",
  "Знаток искусства",
];

const TIME_OPTIONS = [
  { value: "", label: "Не знаю / не важно" },
  { value: "60", label: "≈ 1 час" },
  { value: "90", label: "≈ 1,5 часа" },
  { value: "120", label: "≈ 2 часа" },
];

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RouteResponse }
  | { status: "error"; error: string };

const inputClass =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none";
const labelClass = "mb-1 block text-sm font-medium text-gray-700";
const buttonClass =
  "rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50";

export function RouteForm() {
  const [audience, setAudience] = useState(AUDIENCES[0]);
  const [timeMinutes, setTimeMinutes] = useState("");
  const [interests, setInterests] = useState("");
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setState({ status: "loading" });
    try {
      const data = await buildRoute({
        audience,
        time_minutes: timeMinutes ? Number(timeMinutes) : null,
        interests,
      });
      setState({ status: "success", data });
    } catch (error: unknown) {
      setState({ status: "error", error: error instanceof Error ? error.message : String(error) });
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div>
          <label htmlFor="audience" className={labelClass}>
            Кто вы?
          </label>
          <select id="audience" className={inputClass} value={audience} onChange={(e) => setAudience(e.target.value)}>
            {AUDIENCES.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="time" className={labelClass}>
            Сколько у вас времени?
          </label>
          <select id="time" className={inputClass} value={timeMinutes} onChange={(e) => setTimeMinutes(e.target.value)}>
            {TIME_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="interests" className={labelClass}>
            Что вам ближе? (необязательно)
          </label>
          <input
            id="interests"
            className={inputClass}
            placeholder="Например: истории о людях, красивые вещи, что-то необычное"
            value={interests}
            onChange={(e) => setInterests(e.target.value)}
          />
        </div>

        <button type="submit" className={buttonClass} disabled={state.status === "loading"}>
          {state.status === "loading" ? "Строю маршрут…" : "Построить маршрут"}
        </button>
      </form>

      {state.status === "loading" && <p className="text-gray-500">Искусствовед-переводчик подбирает для вас экспонаты…</p>}

      {state.status === "error" && (
        <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
          <p className="font-semibold">Не удалось построить маршрут.</p>
          <p className="text-sm">{state.error}</p>
        </div>
      )}

      {state.status === "success" && <RouteList data={state.data} />}
    </div>
  );
}