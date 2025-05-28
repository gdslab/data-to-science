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
      };
      seasons: string[];
      studyDbId: string;
      studyName: string;
      studyDescription: string;
    }[];
  };
}

interface BreedBaseFormData {
  breedbaseUrl: string;
  programNames?: string;
  studyDbIds?: string;
  studyNames?: string;
}

interface BreedBaseStudy {
  id: string;
  base_url: string;
  study_id: string;
}

export type {
  BreedBaseSearchAPIResponse,
  BreedBaseStudiesAPIResponse,
  BreedBaseFormData,
  BreedBaseStudy,
};
