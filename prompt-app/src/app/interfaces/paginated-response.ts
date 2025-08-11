
export interface PaginatedResponse<T> {
  items: T[];
  totalCount: number;
  skip: number;
  limit: number;
}
