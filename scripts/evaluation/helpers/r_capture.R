options(stringsAsFactors = FALSE)
options(device = function(...) pdf(file = tempfile(fileext = ".pdf")))

# jsonlite is the only required package here. Candidate scripts load their own task-specific libraries when they are sourced below.
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Package 'jsonlite' is required for JSON baseline output. Install via install.packages('jsonlite').")
}

summarize_obj <- function(x) {
  # Convert runtime objects into small JSON-safe summaries for comparison.
  cls <- class(x)[1]
  round_num <- function(v) round(as.numeric(v), 6)

  if (is.data.frame(x)) {
    # Tables are compared by size, column names, missing values, and numeric summaries.
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
    # Matrices are compared by dimensions and basic numeric aggregates.
    out <- list(type = "matrix", dim = dim(x), na_total = sum(is.na(x)))
    if (is.numeric(x)) {
      out$mean <- round_num(mean(x))
      out$sd <- round_num(sd(as.vector(x)))
      out$sum <- round_num(sum(x))
    }
    return(out)
  }

  if (is.factor(x)) {
    # Factors carry categorical structure through levels and level counts.
    tbl <- table(x)
    return(list(type = "factor", length = length(x), levels = levels(x), counts = as.list(as.integer(tbl))))
  }

  if (is.numeric(x) || is.integer(x)) {
    # Numeric vectors use aggregates instead of every element to keep output small.
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
    # Character vectors are compared only by size and rough diversity.
    return(list(type = "character", length = length(x), unique_count = length(unique(x))))
  }

  if (inherits(x, "lm") || inherits(x, "glm")) {
    # Keep model comparison coarse: class plus fitted coefficients.
    return(list(type = cls, coef = as.list(round_num(coef(x)))))
  }

  if (inherits(x, "tune")) {
    # e1071::tune stores the selected parameters and best performance here.
    out <- list(type = "tune")
    if (!is.null(x$best.parameters)) out$best_parameters <- as.list(x$best.parameters)
    if (!is.null(x$best.performance)) out$best_performance <- round_num(x$best.performance)
    return(out)
  }

  if (inherits(x, "cv.glmnet")) {
    # glmnet CV objects are represented by their selected regularization values.
    return(list(type = "cv.glmnet", lambda_min = round_num(x$lambda.min), lambda_1se = round_num(x$lambda.1se)))
  }

  if (inherits(x, "gbm")) {
    # GBM objects are represented by their top feature-importance entries.
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
    # Generic lists are too broad to compare deeply, so keep length and names.
    return(list(type = "list", length = length(x), names = names(x)))
  }

  # Fallback for unsupported objects keeps their class and length visible.
  return(list(type = cls, length = length(x)))
}

# The Python orchestrator passes paths through environment variables so this helper can stay as a normal R file instead of generated string code.
repo_root <- Sys.getenv("BASELINE_REPO_ROOT")
script_path <- Sys.getenv("BASELINE_SCRIPT")
if (!nzchar(repo_root) || !nzchar(script_path)) {
  stop("BASELINE_REPO_ROOT and BASELINE_SCRIPT must be set.")
}

setwd(repo_root)

# Source the candidate in an isolated environment so we summarize only objects created by the candidate, not helper internals.
candidate_env <- new.env(parent = globalenv())
captured <- capture.output(source(script_path, local = candidate_env))

# List candidate-created object names in stable order, then summarize the data/model objects left in the candidate env.
objs <- sort(ls(envir = candidate_env))
# Build one named summary entry per object created by the candidate script.
out <- list()
for (nm in objs) {
  # Retrieve the object by name from the isolated candidate environment.
  val <- get(nm, envir = candidate_env)
  # Functions are implementation details, not runtime outputs to compare.
  if (is.function(val)) next
  # Store the compact JSON-safe summary under the original object name.
  out[[nm]] <- summarize_obj(val)
}

cat("---SCRIPT_OUTPUT_START---\n")
if (length(captured) > 0) cat(paste(captured, collapse = "\n"))
cat("\n---SCRIPT_OUTPUT_END---\n")
# Markers let the Python orchestrator separate script output from summary JSON.
cat("---SUMMARY_JSON_START---\n")
jsonlite::write_json(out, path = stdout(), auto_unbox = TRUE, na = "null")
cat("\n---SUMMARY_JSON_END---\n")
