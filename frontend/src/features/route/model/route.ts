export type RouteRequest = {
  audience: string;
  time_minutes?: number | null;
  interests?: string;
};

export type RouteStop = {
  id: string;
  name: string;
  author: string;
  why: string;
  story: string;
  fun_fact: string;
  quest: string;
  /** Путь к фото экспоната из открытого датасета музея, например `/data/fonds/.../xxx_foto_1_01.jpg`. */
  image: string;
};

export type RouteResponse = {
  intro: string;
  route: RouteStop[];
  outro: string;
};