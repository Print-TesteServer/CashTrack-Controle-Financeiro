/**
 * Utilitários para formatação de valores monetários no formato brasileiro
 */

/**
 * Converte string em formato brasileiro (5.111,96) para número (5111.96)
 */
export function parseBrazilianCurrency(value: string): number {
  if (!value) return 0;
  
  // Remove espaços e R$ se existir
  let cleaned = value.trim().replace(/R\$\s*/g, '').trim();
  
  // Se não tem vírgula, trata como inteiro
  if (!cleaned.includes(',')) {
    // Remove pontos (separadores de milhar)
    cleaned = cleaned.replace(/\./g, '');
    return parseFloat(cleaned) || 0;
  }
  
  // Separa por vírgula para pegar decimais
  const parts = cleaned.split(',');
  const integerPart = parts[0].replace(/\./g, ''); // Remove pontos de milhar
  const decimalPart = parts[1] || '00';
  
  // Limita a 2 casas decimais
  const decimals = decimalPart.substring(0, 2).padEnd(2, '0');
  
  return parseFloat(`${integerPart}.${decimals}`) || 0;
}

/**
 * Formata número para formato brasileiro (5111.96 -> "5.111,96")
 */
export function formatBrazilianCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '0,00';
  }
  
  return value.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Formata número para exibição com R$ (5111.96 -> "R$ 5.111,96")
 */
export function formatCurrency(value: number | null | undefined): string {
  return `R$ ${formatBrazilianCurrency(value)}`;
}

/**
 * Formata valor para input (aceita tanto ponto quanto vírgula como decimal)
 */
export function formatForInput(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) {
    return '';
  }
  
  // Formata com pontos de milhar e vírgula decimal
  return formatBrazilianCurrency(value);
}

/**
 * Adiciona pontos de milhar na parte inteira
 */
function addThousandsSeparator(integerPart: string): string {
  // Remove pontos existentes primeiro
  const cleaned = integerPart.replace(/\./g, '');
  
  // Adiciona pontos a cada 3 dígitos da direita para esquerda
  if (cleaned.length <= 3) {
    return cleaned;
  }
  
  const parts: string[] = [];
  let remaining = cleaned;
  
  while (remaining.length > 3) {
    parts.unshift(remaining.slice(-3));
    remaining = remaining.slice(0, -3);
  }
  
  if (remaining.length > 0) {
    parts.unshift(remaining);
  }
  
  return parts.join('.');
}

/**
 * Processa valor do input para aceitar formato brasileiro
 * Permite digitar pontos como separadores de milhar
 * Permite vírgula como separador decimal
 * Formata automaticamente enquanto digita
 */
export function handleInputChange(value: string): string {
  // Remove tudo exceto números, vírgula e ponto
  // IMPORTANTE: Mantém vírgula e ponto para permitir digitação
  let cleaned = value.replace(/[^\d,.]/g, '');
  
  // Se tem vírgula, separa parte inteira e decimal
  if (cleaned.includes(',')) {
    const parts = cleaned.split(',');
    // Pega apenas a primeira vírgula (ignora múltiplas)
    const integerPart = parts[0];
    const decimalPart = parts.slice(1).join('') || '';
    
    // Remove todos os pontos da parte inteira para recalcular
    const integerOnly = integerPart.replace(/\./g, '');
    
    // Limita a 2 casas decimais
    const limitedDecimals = decimalPart.substring(0, 2);
    
    // Adiciona pontos de milhar na parte inteira
    const formattedInteger = addThousandsSeparator(integerOnly);
    
    // Retorna formatado - sempre inclui vírgula se foi digitada
    // Se não tem decimais ainda, mantém vírgula para permitir continuar digitando
    return limitedDecimals ? `${formattedInteger},${limitedDecimals}` : `${formattedInteger},`;
  }
  
  // Se não tem vírgula, pode ter pontos como separadores de milhar
  // Remove todos os pontos, recalcula e adiciona nos lugares corretos
  const withoutDots = cleaned.replace(/\./g, '');
  
  // Se tem mais de 3 dígitos, adiciona formatação de milhar
  if (withoutDots.length > 3) {
    return addThousandsSeparator(withoutDots);
  }
  
  return withoutDots;
}

