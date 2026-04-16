export interface PaginationQuery {
  page: number;
  limit: number;
}

export interface PaginatedResult<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export function buildPaginatedResult<T>(
  data: T[],
  total: number,
  query: PaginationQuery,
): PaginatedResult<T> {
  const totalPages = Math.max(Math.ceil(total / query.limit), 1);

  return {
    data,
    meta: {
      page: query.page,
      limit: query.limit,
      total,
      totalPages,
    },
  };
}