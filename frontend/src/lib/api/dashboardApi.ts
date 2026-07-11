/**
 * API client for the dashboard module (Story 5-1).
 */
import { DashboardResponse } from "../../types/dashboard";
import { client } from "./client";

export const dashboardApi = {
  /**
   * Fetch HR Admin's dashboard with all assignments and their statuses.
   *
   * Implements AD-6 access control:
   * - Returns 200 OK for HR_ADMIN role
   * - Returns 403 Forbidden for EMPLOYEE role
   * - Returns 401 Unauthorized for unauthenticated requests
   *
   * @param page - Page number (1-indexed), default 1
   * @param pageSize - Rows per page, default 50
   * @returns DashboardResponse with paginated assignments
   */
  async getDashboard(page: number = 1, pageSize: number = 50): Promise<DashboardResponse> {
    const response = await client.get("/dashboard", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};
