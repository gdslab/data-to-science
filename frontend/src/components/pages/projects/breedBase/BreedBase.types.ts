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
      studyDbId: string;
      studyName: string;
      studyDescription: string;
      trialDbId: string;
      trialName: string;
    }[];
  };
}

interface BreedBaseFormData {
  breedbaseUrl: string;
  studyDbIds?: string;
  studyNames?: string;
  trialDbIds?: string;
  trialNames?: string;
}

interface BreedBaseStudy {
  id: string;
  baseUrl: string;
  studyDbId: string;
}

export type {
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseFormData,
  BreedBaseStudy,
};
