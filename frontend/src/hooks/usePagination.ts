import { useState, useEffect, useMemo, useCallback } from 'react'

export interface UsePaginationOptions {
  initialPageSize?: number
  onFilterChange?: any[]
}

export interface UsePaginationReturn {
  currentPage: number
  pageSize: number
  totalCount: number
  setTotalCount: (count: number) => void
  handlePageChange: (page: number) => void
  handlePageSizeChange: (size: number) => void
  skip: number
  limit: number
  resetToFirstPage: () => void
  totalPages: number
}

export function usePagination(options: UsePaginationOptions = {}): UsePaginationReturn {
  const { initialPageSize = 25, onFilterChange = [] } = options

  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [totalCount, setTotalCount] = useState(0)

  // Calculate skip value for API (zero-indexed)
  const skip = useMemo(() => {
    return (currentPage - 1) * pageSize
  }, [currentPage, pageSize])

  // Alias for clarity in API calls
  const limit = useMemo(() => pageSize, [pageSize])

  // Calculate total pages
  const totalPages = useMemo(() => {
    return Math.ceil(totalCount / pageSize) || 1
  }, [totalCount, pageSize])

  // Handle page changes with validation
  const handlePageChange = useCallback((page: number) => {
    // Validate page number
    if (page < 1) {
      setCurrentPage(1)
      return
    }

    const maxPage = Math.ceil(totalCount / pageSize) || 1
    if (page > maxPage) {
      setCurrentPage(maxPage)
      return
    }

    setCurrentPage(page)
  }, [totalCount, pageSize])

  // Handle page size changes
  const handlePageSizeChange = useCallback((size: number) => {
    setPageSize(size)
    // Reset to page 1 when page size changes
    setCurrentPage(1)
  }, [])

  // Reset to first page
  const resetToFirstPage = useCallback(() => {
    setCurrentPage(1)
  }, [])

  // Auto-reset to page 1 when filters change
  useEffect(() => {
    if (onFilterChange.length > 0) {
      setCurrentPage(1)
    }
  }, onFilterChange) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    currentPage,
    pageSize,
    totalCount,
    setTotalCount,
    handlePageChange,
    handlePageSizeChange,
    skip,
    limit,
    resetToFirstPage,
    totalPages
  }
}
