export type UserRole = "patient" | "caregiver";

export type ApiStatus<T> = {
  data: T | null;
  isLoading: boolean;
  error: string | null;
};
