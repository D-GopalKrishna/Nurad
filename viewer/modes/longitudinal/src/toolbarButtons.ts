import { toolbarButtons as basicToolbarButtons } from '@ohif/mode-basic';
import { toolbarButtons as segmentationToolbarButtons } from '@ohif/mode-segmentation';

// Basic Viewer keeps all of its existing measurement/navigation buttons, and
// gains the segmentation-editing buttons (Brush, Eraser, Threshold, contour
// tools, labelmap/contour utilities) that otherwise only exist in the
// unused "Segmentation" mode. Where an id exists in both (shared nav
// buttons like Zoom/Pan/WindowLevel), basic's definition wins - the two are
// equivalent where they overlap.
const basicIds = new Set(basicToolbarButtons.map(button => button.id));
const segmentationOnlyButtons = segmentationToolbarButtons.filter(
  button => !basicIds.has(button.id)
);

export const toolbarButtons = [...basicToolbarButtons, ...segmentationOnlyButtons];

export default toolbarButtons;
