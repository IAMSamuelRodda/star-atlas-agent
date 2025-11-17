/**
 * Error handling utilities
 *
 * Provides consistent, actionable error messages for MCP tools.
 * All error messages follow best practices:
 * - Start with "Error: " prefix
 * - Explain what went wrong clearly
 * - Suggest next steps when possible
 * - Avoid technical jargon
 * - Be actionable for LLM agents
 */

import axios, { AxiosError } from "axios";

/**
 * Convert any error to a user-friendly error message string
 *
 * @param error Unknown error object
 * @param context Optional context about where the error occurred
 * @returns User-friendly error message
 */
export function handleError(error: unknown, context?: string): string {
  const prefix = context ? `Error in ${context}: ` : "Error: ";

  // Handle axios/HTTP errors
  if (axios.isAxiosError(error)) {
    return prefix + handleAxiosError(error);
  }

  // Handle standard Error objects
  if (error instanceof Error) {
    return prefix + error.message;
  }

  // Handle unknown error types
  return prefix + `Unexpected error: ${String(error)}`;
}

/**
 * Handle axios/HTTP-specific errors
 */
function handleAxiosError(error: AxiosError): string {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;

    switch (status) {
      case 400:
        return "Invalid request parameters. Check input values and try again.";

      case 401:
        return "Authentication failed. Check API credentials.";

      case 403:
        return "Permission denied. You don't have access to this resource.";

      case 404:
        return "Resource not found. Check the ID/mint address and try again.";

      case 429:
        return (
          "Rate limit exceeded. Too many requests. " +
          "Please wait 60 seconds before trying again."
        );

      case 500:
      case 502:
      case 503:
      case 504:
        return (
          "API service is temporarily unavailable. " +
          "Try again in a few minutes. If the problem persists, check service status."
        );

      default:
        return `API request failed with status ${status}. Try again later.`;
    }
  } else if (error.code === "ECONNABORTED") {
    return (
      "Request timed out. The server took too long to respond. " +
      "Try again or check your network connection."
    );
  } else if (error.code === "ENOTFOUND" || error.code === "ECONNREFUSED") {
    return (
      "Cannot connect to API server. " +
      "Check your network connection and try again."
    );
  } else if (error.code === "ERR_NETWORK") {
    return (
      "Network error occurred. " +
      "Check your internet connection and try again."
    );
  }

  return `Network request failed: ${error.message}`;
}

/**
 * Create a not found error message
 */
export function notFoundError(resourceType: string, identifier: string): string {
  return (
    `Error: ${resourceType} not found for identifier '${identifier}'. ` +
    `Verify the ID/mint address is correct and try again.`
  );
}

/**
 * Create a validation error message
 */
export function validationError(field: string, issue: string): string {
  return `Error: Invalid ${field}. ${issue}`;
}

/**
 * Create an empty results message (not technically an error)
 */
export function emptyResultsMessage(searchCriteria: string): string {
  return (
    `No results found matching ${searchCriteria}. ` +
    `Try broader search criteria or different filters.`
  );
}
