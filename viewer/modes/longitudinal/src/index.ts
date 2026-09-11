import i18n from 'i18next';
import { id } from './id';
import initToolGroups from './initToolGroups';
import { toolbarButtons } from './toolbarButtons';
import {
  ohif,
  cornerstone,
  dicomsr,
  dicomvideo,
  basicLayout,
  basicRoute,
  toolbarSections as basicToolbarSections,
  onModeExit,
  extensionDependencies as basicDependencies,
  mode as basicMode,
  modeInstance as basicModeInstance,
} from '@ohif/mode-basic';

export const tracked = {
  measurements: '@ohif/extension-measurement-tracking.panelModule.trackedMeasurements',
  thumbnailList: '@ohif/extension-measurement-tracking.panelModule.seriesList',
  viewport: '@ohif/extension-measurement-tracking.viewportModule.cornerstone-tracked',
};

export const extensionDependencies = {
  // Can derive the versions at least process.env.from npm_package_version
  ...basicDependencies,
  '@ohif/extension-measurement-tracking': '^3.0.0',
};

// Adds the segmentation-editing toolbox sections (labelmap/contour tool
// groups + their utilities) on top of basic's sections, so Basic Viewer's
// toolbar can expose them once enableSegmentationEdit is on below. Matching
// cornerstone tool-group registrations for these tools live in
// initToolGroups.ts. See .vscode/plan/01-ohif-capability-expansion.md.
export const toolbarSections = {
  ...basicToolbarSections,
  labelMapSegmentationToolbox: ['LabelMapTools'],
  contourSegmentationToolbox: ['ContourTools'],
  LabelMapTools: [
    'LabelmapSlicePropagation',
    'BrushTools',
    'MarkerLabelmap',
    'RegionSegmentPlus',
    'Shapes',
    'LabelMapEditWithContour',
  ],
  ContourTools: [
    'PlanarFreehandContourSegmentationTool',
    'SculptorTool',
    'SplineContourSegmentationTool',
    'LivewireContourSegmentationTool',
  ],
  labelMapSegmentationUtilities: ['LabelMapUtilities'],
  contourSegmentationUtilities: ['ContourUtilities'],
  LabelMapUtilities: ['InterpolateLabelmap', 'SegmentBidirectional'],
  ContourUtilities: ['LogicalContourOperations', 'SimplifyContours', 'SmoothContours'],
  BrushTools: ['Brush', 'Eraser', 'Threshold'],
};

// Same as @ohif/mode-basic's onModeEnter (measurementService.clearMeasurements,
// toolbarService registration, enableSegmentationEdit gate, activate-panel
// triggers) but calling this mode's own initToolGroups instead of basic's -
// basic's onModeEnter closes over its own initToolGroups import at module
// scope, so it can't be redirected just by overriding fields on `this`.
function onModeEnter({
  servicesManager,
  extensionManager,
  commandsManager,
  panelService,
  segmentationService,
}: withAppTypes) {
  const { measurementService, toolbarService, toolGroupService, customizationService } =
    servicesManager.services;

  measurementService.clearMeasurements();

  initToolGroups(extensionManager, toolGroupService, commandsManager);

  toolbarService.register(this.toolbarButtons);

  for (const [key, section] of Object.entries(this.toolbarSections)) {
    toolbarService.updateSection(key, section);
  }

  if (!this.enableSegmentationEdit) {
    customizationService.setCustomizations({
      'panelSegmentation.disableEditing': {
        $set: true,
      },
    });
  }

  if (this.activatePanelTrigger) {
    this._activatePanelTriggersSubscriptions = [
      ...panelService.addActivatePanelTriggers(
        cornerstone.segmentation,
        [
          {
            sourcePubSubService: segmentationService,
            sourceEvents: [segmentationService.EVENTS.SEGMENTATION_ADDED],
          },
        ],
        true
      ),
      ...panelService.addActivatePanelTriggers(
        cornerstone.measurements,
        [
          {
            sourcePubSubService: measurementService,
            sourceEvents: [
              measurementService.EVENTS.MEASUREMENT_ADDED,
              measurementService.EVENTS.RAW_MEASUREMENT_ADDED,
            ],
          },
        ],
        true
      ),
      true,
    ];
  }
}

export const longitudinalInstance = {
  ...basicLayout,
  id: ohif.layout,
  props: {
    ...basicLayout.props,
    leftPanels: [tracked.thumbnailList],
    rightPanels: [cornerstone.segmentation, tracked.measurements],
    viewports: [
      {
        namespace: tracked.viewport,
        // Re-use the display sets from basic
        displaySetsToDisplay: basicLayout.props.viewports[0].displaySetsToDisplay,
      },
      ...basicLayout.props.viewports,
      ],
    }
  };


export const longitudinalRoute =
    {
      ...basicRoute,
      path: 'longitudinal',
        /*init: ({ servicesManager, extensionManager }) => {
          //defaultViewerRouteInit
        },*/
      layoutInstance: longitudinalInstance,
    };

export const modeInstance = {
    ...basicModeInstance,
    // TODO: We're using this as a route segment
    // We should not be.
    id,
    routeName: 'viewer',
    displayName: i18n.t('Modes:Basic Viewer'),
    routes: [
      longitudinalRoute
    ],
    extensions: extensionDependencies,
    toolbarButtons,
    toolbarSections,
    onModeEnter,
    onModeExit,
    // Turns on segmentation editing (brush/scissors/contour tools, labelmap
    // and contour utilities) - basic defaults this to false.
    enableSegmentationEdit: true,
  };

const mode = {
  ...basicMode,
  id,
  modeInstance,
  extensionDependencies,
};

export default mode;
export { initToolGroups, toolbarButtons };
