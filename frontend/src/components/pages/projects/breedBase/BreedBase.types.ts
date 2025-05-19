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

interface BreedBaseTrial {
  id: string;
  base_url: string;
  trial_id: string;
}

export type {
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseFormData,
  BreedBaseTrial,
};
