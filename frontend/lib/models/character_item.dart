// Data model to represent the data from the API
class CharacterItem {
  final int id;
  final String name;
  final String characterType;

  CharacterItem({
    required this.id,
    required this.name,
    required this.characterType,
  });

  // Factory constructor to create a CardItem from JSON.
  factory CharacterItem.fromJson(Map<String, dynamic> json) {
    try {
      return CharacterItem(
        id: json['id'] as int,
        name: json['name'] as String,
        characterType: json['character_type'] as String,
      );
    } catch (e) {
      // Re-throw the exception to let the caller handle it
      throw FormatException('Failed to parse CharacterItem: $e');
    }
  }
}
