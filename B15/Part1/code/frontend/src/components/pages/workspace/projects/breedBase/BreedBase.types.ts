interface BreedBaseSearchAPIResponse {
  result: {
    searchResultsDbId: string;
  };
}

interface BreedBaseStudiesAPIResponse {
  metadata: {
    pagination: {
      currentPage: number;
      pageSize: number;
      totalCount: number;
      totalPages: number;
    };
  };
  result: {
    data: {
      additionalInfo: {
        programName?: string;
        description?: string;
      };
      programName?: string;
      seasons: (string | { seasonDbId?: string; year?: string; season?: string })[];
      studyDbId: string;
      studyName: string;
      studyDescription?: string;
    }[];
  };
}

interface BreedBaseFormData {
  breedbaseUrl: string;
  programNames?: string;
  studyDbIds?: string;
  studyNames?: string;
  year?: string;
}

interface BreedBaseStudy {
  id: string;
  base_url: string;
  study_id: string;
}

interface BreedBaseOAuthMessage {
  type: 'breedbase-oauth-callback';
  status: string;
  accessToken?: string;
  error?: string;
}

type BreedBaseOAuthStatus = 'none' | 'authenticated' | 'validating' | 'expired';

export type {
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseFormData,
  BreedBaseStudy,
  BreedBaseOAuthMessage,
  BreedBaseOAuthStatus,
};
