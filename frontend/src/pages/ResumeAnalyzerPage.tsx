import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Upload,
  FileText,
  CheckCircle,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  Hash,
} from 'lucide-react';
import { parseResume, recommendJobs } from '../api';
import type { ResumeParseResponse, JobRecommendItem, ApiError } from '../api/types';
import { SkillPill } from '../components/common/SkillPill';
import { Alert } from '../components/common/Alert';

export const ResumeAnalyzerPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState<string>('');
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [validationFeedback, setValidationFeedback] = useState<{
    type: 'invalid' | 'unreadable' | 'uncertain' | 'error';
    title: string;
    message: string;
  } | null>(null);
  const [parseResult, setParseResult] = useState<ResumeParseResponse | null>(null);

  // Recommendations state
  const [recs, setRecs] = useState<JobRecommendItem[]>([]);
  const [loadingRecs, setLoadingRecs] = useState<boolean>(false);

  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMsg(null);
    setValidationFeedback(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.docx', '.txt'].includes(ext)) {
        setErrorMsg(`Unsupported file type '${ext}'. Please upload a .pdf, .docx, or .txt file.`);
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setErrorMsg('File size exceeds the 10MB limit.');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleAnalyze = async () => {
    setErrorMsg(null);
    setValidationFeedback(null);
    setParseResult(null);
    setRecs([]);

    if (activeTab === 'upload' && !selectedFile) {
      setErrorMsg('Please select a file to upload.');
      return;
    }

    if (activeTab === 'paste' && rawText.trim().length < 10) {
      setErrorMsg('Please enter at least 10 characters of resume text.');
      return;
    }

    setIsParsing(true);
    try {
      const result = await parseResume({
        file: activeTab === 'upload' ? selectedFile || undefined : undefined,
        rawText: activeTab === 'paste' ? rawText.trim() : undefined,
        filename: activeTab === 'upload' ? selectedFile?.name : 'pasted_resume.txt',
      });
      setParseResult(result);

      // Auto-fetch top 3 recommendations based on extracted text (uses resume_id for full text)
      setLoadingRecs(true);
      recommendJobs({
        resume_id: result.resume_id,
        resume_text: result.extracted_text_preview || rawText || 'Software Developer',
        top_n: 3,
      })
        .then((res) => setRecs(res.recommendations))
        .catch(() => setRecs([]))
        .finally(() => setLoadingRecs(false));
    } catch (err: any) {
      const apiErr = err as ApiError;
      const detail =
        typeof apiErr.detail === 'string'
          ? apiErr.detail
          : Array.isArray(apiErr.detail) && apiErr.detail[0]?.msg
            ? apiErr.detail[0].msg
            : apiErr.message || 'Failed to parse resume. Check document format.';

      const detailLower = detail.toLowerCase();
      if (
        detailLower.includes('does not appear to be a resume') ||
        detailLower.includes('research paper') ||
        detailLower.includes('invoice') ||
        detailLower.includes('assignment')
      ) {
        setValidationFeedback({
          type: 'invalid',
          title: 'Invalid Document',
          message: detail,
        });
      } else if (
        detailLower.includes('readable text could not be extracted') ||
        detailLower.includes('unreadable') ||
        detailLower.includes('scanned pdf')
      ) {
        setValidationFeedback({
          type: 'unreadable',
          title: 'Unreadable Document',
          message: detail,
        });
      } else if (
        detailLower.includes('could not be verified as a resume') ||
        detailLower.includes('clearer or more complete resume') ||
        detailLower.includes('ambiguous')
      ) {
        setValidationFeedback({
          type: 'uncertain',
          title: 'Uncertain Document',
          message: detail,
        });
      } else {
        setErrorMsg(detail);
      }
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Resume Parser & NLP Classifier
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Extract technical skills via word-boundary regex and classify resumes into 25 categories
          with multiclass Logistic Regression.
        </p>
      </div>

      {validationFeedback && (
        <Alert
          type={validationFeedback.type === 'invalid' || validationFeedback.type === 'error' ? 'error' : 'warning'}
          title={validationFeedback.title}
          onClose={() => setValidationFeedback(null)}
        >
          {validationFeedback.message}
        </Alert>
      )}

      {errorMsg && (
        <Alert type="error" onClose={() => setErrorMsg(null)}>
          {errorMsg}
        </Alert>
      )}

      {/* Input Selector Card */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden transition-colors">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-200 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-3 px-4 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${
              activeTab === 'upload'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/40 dark:bg-indigo-950/40'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
          >
            <Upload className="h-4 w-4" />
            <span>Upload Document (.pdf, .docx, .txt)</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('paste')}
            className={`flex-1 py-3 px-4 text-sm font-semibold flex items-center justify-center gap-2 border-b-2 transition-colors ${
              activeTab === 'paste'
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400 bg-indigo-50/40 dark:bg-indigo-950/40'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>Paste Resume Text</span>
          </button>
        </div>

        <div className="p-6">
          {activeTab === 'upload' ? (
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-8 text-center hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors">
              <input
                type="file"
                id="resume-file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="resume-file" className="cursor-pointer flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mb-3">
                  <Upload className="h-6 w-6" />
                </div>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">
                  {selectedFile ? selectedFile.name : 'Click to select or drag and drop a resume'}
                </span>
                <span className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  Supported formats: PDF, DOCX, TXT (Maximum file size: 10MB)
                </span>
                {selectedFile && (
                  <span className="mt-3 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Selected: {(selectedFile.size / 1024).toFixed(1)} KB
                  </span>
                )}
              </label>
            </div>
          ) : (
            <div>
              <label htmlFor="raw-text" className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                Paste Resume Content
              </label>
              <textarea
                id="raw-text"
                rows={8}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                placeholder="Paste the plain text of your resume here (experience, skills, education)..."
                className="w-full p-3.5 border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-xl text-sm placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-indigo-600 font-mono"
              />
              <div className="flex justify-between text-xs text-slate-400 dark:text-slate-500 mt-1">
                <span>Minimum 10 characters</span>
                <span>{rawText.length} characters</span>
              </div>
            </div>
          )}

          <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800 flex-wrap gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              <span>PII is automatically masked; binaries are isolated in private storage.</span>
            </div>

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={isParsing}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
            >
              <Sparkles className="h-4 w-4" />
              <span>{isParsing ? 'Extracting & Classifying...' : 'Run Analysis'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Parse Results Presentation */}
      {parseResult && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4 mb-5 flex-wrap gap-2">
              <div>
                <span className="text-xs font-mono text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Verification Fingerprint
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <Hash className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                  <span className="font-mono text-xs text-slate-700 dark:text-slate-300 select-all">
                    {parseResult.sha256}
                  </span>
                </div>
              </div>

              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Document: <strong className="text-slate-800 dark:text-slate-200">{parseResult.original_filename}</strong> ({parseResult.file_size_bytes} bytes)
              </span>
            </div>

            {parseResult.validation && (
              <div className="mb-5 p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
                  <span className="text-xs font-semibold text-emerald-900 dark:text-emerald-200">
                    Validated Resume ({parseResult.validation.confidence_category} Confidence)
                  </span>
                </div>
                {parseResult.validation.detected_sections && parseResult.validation.detected_sections.length > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-700 dark:text-emerald-300">
                    <span className="font-medium text-emerald-800 dark:text-emerald-200">Sections identified:</span>
                    <span>{parseResult.validation.detected_sections.join(', ')}</span>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Classification Prediction */}
              <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Predicted Job Category
                </span>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                  {parseResult.predicted_category}
                </h3>
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                    Model Confidence:
                  </span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950 text-indigo-800 dark:text-indigo-300">
                    {(parseResult.category_confidence * 100).toFixed(1)}%
                  </span>
                </div>

                {/* Top Alternative Probabilities */}
                {parseResult.category_probabilities && Object.keys(parseResult.category_probabilities).length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700">
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-2">
                      Top Category Probabilities:
                    </p>
                    <div className="space-y-1.5">
                      {Object.entries(parseResult.category_probabilities).map(([cat, prob]) => (
                        <div key={cat} className="flex items-center justify-between text-xs">
                          <span className="text-slate-700 dark:text-slate-300 truncate max-w-[200px]">{cat}</span>
                          <span className="font-mono text-slate-500 dark:text-slate-400">{(prob * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Extracted Skills */}
              <div className="p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Extracted Technical Skills ({parseResult.extracted_skills.length})
                  </span>
                  <div className="mt-3 flex flex-wrap gap-1.5 max-h-48 overflow-y-auto">
                    {parseResult.extracted_skills.length > 0 ? (
                      parseResult.extracted_skills.map((skill) => (
                        <SkillPill key={skill} name={skill} variant="matched" />
                      ))
                    ) : (
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        No technical skills matched the current master skill lexicon.
                      </p>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-400 dark:text-slate-500">
                  Extracted via isolated word boundaries to prevent token collision (e.g. isolating AI from mail).
                </div>
              </div>
            </div>

            {/* PII-Redacted Text Preview */}
            <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-2">
                Sanitized Content Preview (PII Redacted)
              </span>
              <pre className="p-3 bg-slate-100 dark:bg-slate-800/80 rounded-lg text-xs font-mono text-slate-800 dark:text-slate-200 whitespace-pre-wrap max-h-36 overflow-y-auto border border-slate-200 dark:border-slate-700">
                {parseResult.extracted_text_preview}
              </pre>
            </div>
          </div>

          {/* Quick Match Recommendations based on this Resume */}
          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 shadow-xs transition-colors">
            <h3 className="font-bold text-slate-900 dark:text-white text-base mb-1">
              Top Ranked Job Recommendations for this Resume
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Scored with TF-IDF cosine similarity against processed repository job records
            </p>

            {loadingRecs ? (
              <div className="py-6 text-center text-sm text-slate-400 dark:text-slate-500">Ranking jobs...</div>
            ) : recs.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500">No immediate matches found.</p>
            ) : (
              <div className="space-y-3">
                {recs.map((rec) => (
                  <div
                    key={rec.job_id}
                    className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between flex-wrap gap-4"
                  >
                    <div>
                      <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-100 dark:border-indigo-800">
                        {rec.category}
                      </span>
                      <h4 className="font-semibold text-slate-900 dark:text-white text-sm mt-1">{rec.title}</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{rec.company} • {rec.location}</p>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 dark:text-slate-500 block">Fit Index</span>
                        <span className="font-bold text-slate-900 dark:text-white text-sm">{rec.fit_score}%</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const resumeId = parseResult?.resume_id || '';
                          const resumeContent = parseResult?.extracted_text_preview || rawText || '';
                          const jobDesc = rec.description || rec.skills || '';
                          navigate(
                            `/matching?job_title=${encodeURIComponent(rec.title)}` +
                            `&job_text=${encodeURIComponent(jobDesc)}` +
                            `&job_skills=${encodeURIComponent(rec.skills)}` +
                            (resumeId ? `&resume_id=${encodeURIComponent(resumeId)}` : '') +
                            `&resume_text=${encodeURIComponent(resumeContent)}` +
                            `&text_sim=${encodeURIComponent(rec.similarity_score.toString())}`
                          );
                        }}
                        className="text-xs font-semibold px-3 py-1.5 rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors flex items-center gap-1"
                      >
                        Details <ArrowRight className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
