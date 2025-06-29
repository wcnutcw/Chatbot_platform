// Thailand timezone utilities
export const THAILAND_TIMEZONE = 'Asia/Bangkok';

/**
 * Format date to Thailand time string
 */
export const formatThailandTime = (date: Date | string, options?: Intl.DateTimeFormatOptions): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: THAILAND_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  };

  return dateObj.toLocaleString('th-TH', { ...defaultOptions, ...options });
};

/**
 * Format date to Thailand time with custom format
 */
export const formatThailandDateTime = (date: Date | string): string => {
  return formatThailandTime(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

/**
 * Format date to Thailand date only
 */
export const formatThailandDate = (date: Date | string): string => {
  return formatThailandTime(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

/**
 * Format time to Thailand time only
 */
export const formatThailandTimeOnly = (date: Date | string): string => {
  return formatThailandTime(date, {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

/**
 * Get current Thailand time
 */
export const getCurrentThailandTime = (): Date => {
  return new Date(new Date().toLocaleString("en-US", { timeZone: THAILAND_TIMEZONE }));
};

/**
 * Convert UTC time to Thailand time
 */
export const convertToThailandTime = (utcDate: Date | string): Date => {
  const dateObj = typeof utcDate === 'string' ? new Date(utcDate) : utcDate;
  return new Date(dateObj.toLocaleString("en-US", { timeZone: THAILAND_TIMEZONE }));
};

/**
 * Format relative time in Thailand context
 */
export const formatRelativeThailandTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = getCurrentThailandTime();
  const diffInMs = now.getTime() - dateObj.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInMinutes < 1) {
    return 'เมื่อสักครู่';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes} นาทีที่แล้ว`;
  } else if (diffInHours < 24) {
    return `${diffInHours} ชั่วโมงที่แล้ว`;
  } else if (diffInDays < 7) {
    return `${diffInDays} วันที่แล้ว`;
  } else {
    return formatThailandDate(dateObj);
  }
};

/**
 * Format chat message time for Thailand
 */
export const formatChatTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = getCurrentThailandTime();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const messageDate = new Date(dateObj.getFullYear(), dateObj.getMonth(), dateObj.getDate());
  
  if (messageDate.getTime() === today.getTime()) {
    // Today - show only time
    return formatThailandTimeOnly(dateObj);
  } else {
    // Other days - show date and time
    return formatThailandDateTime(dateObj);
  }
};