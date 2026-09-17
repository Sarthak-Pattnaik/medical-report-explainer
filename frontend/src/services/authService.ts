import api from "@/lib/api";
import type {
  LoginData,
  RegisterData,
  TokenResponse,
  User,
} from "@/types/auth";

export async function registerUser(
  data: RegisterData
): Promise<User> {
  const response = await api.post<User>(
    "/auth/register",
    data
  );

  return response.data;
}


export async function loginUser(
  data: LoginData
): Promise<TokenResponse> {
  const formData = new URLSearchParams();

  formData.append("username", data.username);
  formData.append("password", data.password);

  const response = await api.post<TokenResponse>(
    "/auth/login",
    formData,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    }
  );

  return response.data;
}


export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");

  return response.data;
}