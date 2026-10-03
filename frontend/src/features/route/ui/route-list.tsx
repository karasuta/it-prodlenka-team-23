import type { RouteResponse, RouteStop } from "../model/route";

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

function buildingLabel(building: string): string {
  return building || "Экспозиция";
}

function StopCard({ stop, index }: { stop: RouteStop; index: number }) {
  return (
    <li className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <div className="flex flex-col sm:flex-row">
        <div className="h-48 w-full shrink-0 bg-gray-100 sm:h-auto sm:w-56">
          {stop.image && (
            <img
              src={imageUrl(stop.image)}
              alt={stop.name}
              loading="lazy"
              className="h-full w-full object-contain p-2"
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
          {stop.location && <p className="text-sm text-gray-500">{stop.location}</p>}

          <p className="text-gray-800">{stop.story}</p>

          {stop.why && (
            <p className="text-sm text-gray-600">
              <span className="font-semibold">Это интересно: </span>
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
  );
}

export function RouteList({ data }: { data: RouteResponse }) {
  return (
    <section className="flex flex-col gap-4">
      <p className="text-lg font-medium text-gray-800">{data.intro}</p>

      {data.groups.map((group, groupIndex) => {
        // Сквозная нумерация остановок: смещение = сумма остановок в предыдущих группах.
        const offset = data.groups
          .slice(0, groupIndex)
          .reduce((sum, prev) => sum + prev.stops.length, 0);

        return (
          <div key={group.building} className="flex flex-col gap-3">
            <h2 className="mt-2 text-lg font-bold text-gray-900">
              {buildingLabel(group.building)}
            </h2>

            <ol className="flex list-none flex-col gap-5">
              {group.stops.map((stop, index) => (
                <StopCard key={stop.id} stop={stop} index={offset + index} />
              ))}
            </ol>
          </div>
        );
      })}

      <p className="rounded-xl bg-blue-50 p-4 text-gray-800">{data.outro}</p>
    </section>
  );
}