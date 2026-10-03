import type { RouteResponse } from "../model/route";

// Фото экспонатов лежат в открытом датасете Пушкинского музея. Бэкенд
// возвращает путь из датасета (например, /data/fonds/.../xxx_foto_1_01.jpg),
// а здесь мы собираем полный URL. Хост можно переопределить через
// VITE_MUSEUM_IMAGE_BASE_URL (например, для локальной папки с копией фото).
const MUSEUM_IMAGE_BASE_URL = import.meta.env.VITE_MUSEUM_IMAGE_BASE_URL ?? "https://pushkinmuseum.art";

function imageUrl(path: string): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${MUSEUM_IMAGE_BASE_URL}${path}`;
}

export function RouteList({ data }: { data: RouteResponse }) {
  return (
    <section className="flex flex-col gap-4">
      <p className="text-lg font-medium text-gray-800">{data.intro}</p>

      <ol className="flex list-none flex-col gap-5">
        {data.route.map((stop, index) => (
          <li key={stop.id} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="flex flex-col sm:flex-row">
              <div className="h-48 w-full shrink-0 bg-gray-100 sm:h-auto sm:w-56">
                {stop.image && (
                  <img
                    src={imageUrl(stop.image)}
                    alt={stop.name}
                    loading="lazy"
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      // Если картинка не загрузилась — прячем её, остаётся серый фон.
                      e.currentTarget.style.display = "none";
                    }}
                  />
                )}
              </div>
              <div className="flex flex-col gap-2 p-5">
                <p className="text-sm font-semibold text-blue-700">Остановка {index + 1}</p>
                <h3 className="text-xl font-bold text-gray-900">{stop.name}</h3>
                {stop.author && <p className="text-sm text-gray-500">{stop.author}</p>}

                <p className="text-gray-800">{stop.story}</p>

                {stop.why && (
                  <p className="text-sm text-gray-600">
                    <span className="font-semibold">Почему это вам: </span>
                    {stop.why}
                  </p>
                )}

                {stop.fun_fact && (
                  <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
                    <span className="font-semibold">Зацепка: </span>
                    {stop.fun_fact}
                  </p>
                )}

                {stop.quest && (
                  <p className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-900">
                    <span className="font-semibold">Квест: </span>
                    {stop.quest}
                  </p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ol>

      <p className="rounded-xl bg-blue-50 p-4 text-gray-800">{data.outro}</p>
    </section>
  );
}