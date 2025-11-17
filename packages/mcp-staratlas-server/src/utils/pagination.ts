/**
 * Pagination utilities for MCP tools
 *
 * Implements cursor-based pagination per MCP specification
 * with character limit enforcement and truncation handling.
 */

import { CHARACTER_LIMIT } from "../constants.js";
import type { PaginatedResponse, PaginationParams } from "../schemas/common.js";

/**
 * Paginate an array of items with character limit enforcement
 *
 * @param items Array of items to paginate
 * @param params Pagination parameters (limit, offset)
 * @param formatItem Function to convert item to string representation
 * @param maxCharacters Maximum characters allowed in response (default: CHARACTER_LIMIT)
 * @returns Paginated response with truncation info
 */
export function paginateItems<T>(
  items: T[],
  params: PaginationParams,
  formatItem?: (item: T) => string,
  maxCharacters: number = CHARACTER_LIMIT
): PaginatedResponse<T> {
  const { limit, offset } = params;
  const total = items.length;

  // Calculate pagination bounds
  const start = Math.min(offset, total);
  const end = Math.min(start + limit, total);
  const paginatedItems = items.slice(start, end);

  // Check if more results exist
  const hasMore = end < total;
  const nextOffset = hasMore ? end : undefined;

  // Create base response
  const response: PaginatedResponse<T> = {
    total,
    count: paginatedItems.length,
    offset,
    items: paginatedItems,
    has_more: hasMore,
    next_offset: nextOffset,
  };

  // If formatItem function provided, check character limit
  if (formatItem) {
    const formatted = paginatedItems.map(formatItem).join("");
    if (formatted.length > maxCharacters) {
      // Response too large - reduce items
      const reducedCount = Math.max(1, Math.floor(paginatedItems.length / 2));
      const reducedItems = paginatedItems.slice(0, reducedCount);

      response.items = reducedItems;
      response.count = reducedItems.length;
      response.has_more = true;
      response.next_offset = offset + reducedItems.length;
      response.truncated = true;
      response.truncation_message =
        `Response truncated from ${paginatedItems.length} to ${reducedItems.length} items ` +
        `to stay within ${maxCharacters} character limit. ` +
        `Use 'offset=${response.next_offset}' to see more results.`;
    }
  }

  return response;
}

/**
 * Filter items based on predicate with pagination
 *
 * @param items Array of all items
 * @param predicate Filter function
 * @param params Pagination parameters
 * @returns Paginated filtered results
 */
export function filterAndPaginate<T>(
  items: T[],
  predicate: (item: T) => boolean,
  params: PaginationParams
): PaginatedResponse<T> {
  const filtered = items.filter(predicate);
  return paginateItems(filtered, params);
}

/**
 * Sort items before pagination
 *
 * @param items Array of items
 * @param compareFn Sort comparison function
 * @param params Pagination parameters
 * @returns Paginated sorted results
 */
export function sortAndPaginate<T>(
  items: T[],
  compareFn: (a: T, b: T) => number,
  params: PaginationParams
): PaginatedResponse<T> {
  const sorted = [...items].sort(compareFn);
  return paginateItems(sorted, params);
}
