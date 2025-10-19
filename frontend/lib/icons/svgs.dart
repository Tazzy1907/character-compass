import 'package:font_awesome_flutter/font_awesome_flutter.dart';

const publicIconMap = {
  // Classic Genres
  'fantasy': FontAwesomeIcons.dragon,
  'sciFi': FontAwesomeIcons.rocket,
  'mystery': FontAwesomeIcons.magnifyingGlass,
  'romance': FontAwesomeIcons.solidHeart,
  'horror': FontAwesomeIcons.ghost,
  'history': FontAwesomeIcons.landmark,
  'western': FontAwesomeIcons.hatCowboy,
  'comics': FontAwesomeIcons.mask,

  // Non-Fiction & Knowledge
  'science': FontAwesomeIcons.atom,
  'biography': FontAwesomeIcons.user,
  'business': FontAwesomeIcons.chartLine,
  'cooking': FontAwesomeIcons.utensils,
  'travel': FontAwesomeIcons.planeDeparture,

  // Arts & Other
  'music': FontAwesomeIcons.music,
  'art': FontAwesomeIcons.palette,
  'poetry': FontAwesomeIcons.penFancy,
};

const iconMap = {
  ...publicIconMap,
  'error': FontAwesomeIcons.triangleExclamation,
};
