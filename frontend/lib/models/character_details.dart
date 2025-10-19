// Model for character data from the API
class CharacterDetails {
  final int id;
  final String name;
  final String bookUrl;
  final String characterType;
  final int? age;
  final String? gender;
  final String? sex;
  final String? race;
  final String? occupation;
  final String? personality;
  final String? appearance;
  final String? backstory;
  final List<String> relationships;
  final List<String> goals;
  final List<String> motivations;

  CharacterDetails({
    required this.id,
    required this.name,
    required this.bookUrl,
    required this.characterType,
    this.age,
    this.gender,
    this.sex,
    this.race,
    this.occupation,
    this.personality,
    this.appearance,
    this.backstory,
    required this.relationships,
    required this.goals,
    required this.motivations,
  });

  // Factory constructor to create a Character from JSON
  factory CharacterDetails.fromJson(Map<String, dynamic> json) {
    return CharacterDetails(
      id: json['id'] as int,
      name: json['name'] as String,
      bookUrl: json['book_url'] as String,
      characterType: json['character_type'] as String,
      age: json['age'] as int?,
      gender: json['gender'] as String?,
      sex: json['sex'] as String?,
      race: json['race'] as String?,
      occupation: json['occupation'] as String?,
      personality: json['personality'] as String?,
      appearance: json['appearance'] as String?,
      backstory: json['backstory'] as String?,
      relationships:
          (json['relationships'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      goals:
          (json['goals'] as List<dynamic>?)?.map((e) => e as String).toList() ??
          [],
      motivations:
          (json['motivations'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
    );
  }

  // Get a brief description of the character
  String get briefDescription {
    List<String> parts = [];
    if (age != null) parts.add('Age $age');
    if (gender != null) parts.add(gender!);
    if (occupation != null && occupation!.isNotEmpty) parts.add(occupation!);
    return parts.join(' • ');
  }

  // Check if character has any content
  bool get hasPersonality => personality != null && personality!.isNotEmpty;
  bool get hasAppearance => appearance != null && appearance!.isNotEmpty;
  bool get hasBackstory => backstory != null && backstory!.isNotEmpty;
  bool get hasRelationships => relationships.isNotEmpty;
  bool get hasGoals => goals.isNotEmpty;
  bool get hasMotivations => motivations.isNotEmpty;
}
