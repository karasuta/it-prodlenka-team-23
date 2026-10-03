import { RouteForm } from "@/features/route";
import { apiUrl } from "@/shared/api";

export function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-6 p-8">
      <h1 className="text-3xl font-bold">Вау-музей, Смотри иначе!</h1>
      <p className="text-gray-600">Маршрут по Пушкинскому музею для тебя</p>
      <RouteForm />
      <p>
        <a href={apiUrl("/docs")} className="text-blue-600 underline hover:text-blue-800">
          API documentation
        </a>
      </p>
    </main>
  );
}