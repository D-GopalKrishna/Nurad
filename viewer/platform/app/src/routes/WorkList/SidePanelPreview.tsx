import React, { useState } from 'react';

import { StudyList, Button, type StudyRow } from '@ohif/ui-next';
import { DicomUpload } from '@ohif/extension-cornerstone';
import { useSeriesFetch } from '../../hooks';

import { StudyListSettingsPopover } from './StudyListSettingsPopover';

type PreviewSeriesView = 'all' | 'thumbnails' | 'list';
const ALLOWED_PREVIEW_SERIES_VIEWS: ReadonlyArray<PreviewSeriesView> = [
  'all',
  'thumbnails',
  'list',
];

export function SidePanelPreview({
  dataSource,
  selected,
  servicesManager,
  onRefresh,
}: {
  dataSource: any;
  selected: StudyRow | null;
  servicesManager: AppTypes.ServicesManager;
  onRefresh?: () => void;
}) {
  const { series, onThumbnailImageError } = useSeriesFetch({ dataSource, selected });
  const { customizationService } = servicesManager.services;
  const thumbnailRendering = dataSource?.getConfig?.()?.thumbnailRendering;
  const thumbnailRequestStrategy =
    dataSource?.getConfig?.()?.thumbnailRequestStrategy || 'bulkDataRetrieve';
  const forceListView =
    thumbnailRendering === 'wadors' ||
    thumbnailRendering === 'thumbnailDirect' ||
    thumbnailRequestStrategy === 'bulkDataRetrieve';

  const customizationSeriesView = customizationService.getCustomization(
    'workList.previewSeriesView'
  );
  const configuredSeriesView: PreviewSeriesView = ALLOWED_PREVIEW_SERIES_VIEWS.includes(
    customizationSeriesView as PreviewSeriesView
  )
    ? (customizationSeriesView as PreviewSeriesView)
    : 'all';
  const seriesView: PreviewSeriesView = forceListView ? 'list' : configuredSeriesView;

  const previewProps: PreviewContentProps = {
    study: selected as StudyRow | null,
    series,
    seriesView,
    onThumbnailImageError,
    dataSource,
    onRefresh,
  };

  const renderPreviewContent = customizationService.getCustomization('workList.renderPreviewContent');
  if (typeof renderPreviewContent === 'function') {
    return <>{(renderPreviewContent as RenderPreviewContent)(React, previewProps)}</>;
  }
  return <DefaultPreviewContent {...previewProps} />;
}

export type PreviewContentProps = {
  study: StudyRow | null;
  series: any[];
  seriesView: PreviewSeriesView;
  onThumbnailImageError: (seriesUID: string) => void;
  dataSource?: any;
  onRefresh?: () => void;
};

export type RenderPreviewContent = (
  React: typeof import('react'),
  props: PreviewContentProps
) => React.ReactNode;

function DefaultPreviewContent({
  study,
  series,
  seriesView,
  onThumbnailImageError,
  dataSource,
  onRefresh,
}: PreviewContentProps) {
  // Upload is reachable from the panel header regardless of whether a study
  // is selected - "she keeps copying files around" is the actual ingestion
  // workflow this exists for. See .vscode/plan/02-dashboard-ingestion.md.
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  if (isUploadOpen) {
    return (
      <StudyList.PreviewContainer>
        <StudyList.PreviewHeader>
          <span className="text-foreground text-sm font-medium">Upload DICOM</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsUploadOpen(false)}
          >
            Close
          </Button>
        </StudyList.PreviewHeader>
        <DicomUpload
          dataSource={dataSource}
          onStarted={() => {}}
          onComplete={() => {
            setIsUploadOpen(false);
            onRefresh?.();
          }}
        />
      </StudyList.PreviewContainer>
    );
  }

  return (
    <StudyList.PreviewContainer>
      <StudyList.PreviewHeader>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsUploadOpen(true)}
        >
          Upload
        </Button>
        <StudyListSettingsPopover />
        <StudyList.ClosePreviewButton />
      </StudyList.PreviewHeader>
      <StudyList.PreviewContent
        study={study}
        series={series}
        seriesView={seriesView}
        onThumbnailImageError={onThumbnailImageError}
      />
    </StudyList.PreviewContainer>
  );
}
