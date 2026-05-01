options(stringsAsFactors = FALSE)
options(device = function(...) pdf(file = tempfile(fileext = ".pdf")))

if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Package 'jsonlite' is required for JSON baseline output. Install via install.packages('jsonlite').")
}

summarize_obj <- function(x) {
  cls <- class(x)[1]
  round_num <- function(v) round(as.numeric(v), 6)

  if (is.data.frame(x)) {
    out <- list(type = "data.frame", nrow = nrow(x), ncol = ncol(x), colnames = colnames(x), na_total = sum(is.na(x)))
    num_idx <- vapply(x, is.numeric, logical(1))
    if (any(num_idx)) {
      num <- x[, num_idx, drop = FALSE]
      out$numeric_means <- lapply(num, function(col) round_num(mean(col)))
      out$numeric_sds <- lapply(num, function(col) round_num(sd(col)))
    }
    return(out)
  }

  if (is.matrix(x)) {
    out <- list(type = "matrix", dim = dim(x), na_total = sum(is.na(x)))
    if (is.numeric(x)) {
      out$mean <- round_num(mean(x))
      out$sd <- round_num(sd(as.vector(x)))
      out$sum <- round_num(sum(x))
    }
    return(out)
  }

  if (is.factor(x)) {
    tbl <- table(x)
    return(list(type = "factor", length = length(x), levels = levels(x), counts = as.list(as.integer(tbl))))
  }

  if (is.numeric(x) || is.integer(x)) {
    out <- list(type = "numeric", length = length(x), na_total = sum(is.na(x)))
    if (length(x) > 0) {
      out$mean <- round_num(mean(x, na.rm = TRUE))
      out$sd <- round_num(sd(x, na.rm = TRUE))
      out$sum <- round_num(sum(x, na.rm = TRUE))
      out$min <- round_num(min(x, na.rm = TRUE))
      out$max <- round_num(max(x, na.rm = TRUE))
    }
    return(out)
  }

  if (is.character(x)) {
    return(list(type = "character", length = length(x), unique_count = length(unique(x))))
  }

  if (inherits(x, "lm") || inherits(x, "glm")) {
    return(list(type = cls, coef = as.list(round_num(coef(x)))))
  }

  if (inherits(x, "tune")) {
    out <- list(type = "tune")
    if (!is.null(x$best.parameters)) out$best_parameters <- as.list(x$best.parameters)
    if (!is.null(x$best.performance)) out$best_performance <- round_num(x$best.performance)
    return(out)
  }

  if (inherits(x, "cv.glmnet")) {
    return(list(type = "cv.glmnet", lambda_min = round_num(x$lambda.min), lambda_1se = round_num(x$lambda.1se)))
  }

  if (inherits(x, "gbm")) {
    s <- tryCatch(summary(x, plotit = FALSE), error = function(e) NULL)
    out <- list(type = "gbm")
    if (!is.null(s)) {
      s <- s[order(-s$rel.inf), , drop = FALSE]
      top <- head(s, 10)
      out$top_features <- as.list(as.character(top$var))
      out$top_rel_inf <- as.list(round_num(top$rel.inf))
    }
    return(out)
  }

  if (is.list(x)) {
    return(list(type = "list", length = length(x), names = names(x)))
  }

  return(list(type = cls, length = length(x)))
}

repo_root <- Sys.getenv("BASELINE_REPO_ROOT")
script_path <- Sys.getenv("BASELINE_SCRIPT")
if (!nzchar(repo_root) || !nzchar(script_path)) {
  stop("BASELINE_REPO_ROOT and BASELINE_SCRIPT must be set.")
}

setwd(repo_root)

# Source the candidate in an isolated environment so we summarize only objects
# created by the candidate, not helper internals.
candidate_env <- new.env(parent = globalenv())
captured <- capture.output(source(script_path, local = candidate_env))

objs <- sort(ls(envir = candidate_env))
out <- list()
for (nm in objs) {
  val <- get(nm, envir = candidate_env)
  if (is.function(val)) next
  out[[nm]] <- summarize_obj(val)
}

cat("---SCRIPT_OUTPUT_START---\n")
if (length(captured) > 0) cat(paste(captured, collapse = "\n"))
cat("\n---SCRIPT_OUTPUT_END---\n")
cat("---SUMMARY_JSON_START---\n")
jsonlite::write_json(out, path = stdout(), auto_unbox = TRUE, na = "null")
cat("\n---SUMMARY_JSON_END---\n")
