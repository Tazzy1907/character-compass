// Data model to represent the data from the API
class CharacterDetails {
  final int id;
  final String name;
  final String bookUrl;
  final String characterType;
  final String createdAt;
  final String updatedAt;

  final int? age;
  final String? gender;
  final String? sex;
  final String? race;
  final String? occupation;
  final String? personality;
  final String? appearance;
  final String? backstory;
  final List<String>? relationships;
  final List<String>? goals;
  final List<String>? motivations;

  CharacterDetails({
    required this.id,
    required this.name,
    required this.bookUrl,
    required this.characterType,
    required this.createdAt,
    required this.updatedAt,
    this.age,
    this.gender,
    this.sex,
    this.race,
    this.occupation,
    this.personality,
    this.appearance,
    this.backstory,
    this.relationships,
    this.goals,
    this.motivations,
  });

  // Factory constructor to create a CardItem from JSON.
  factory CharacterDetails.fromJson(Map<String, dynamic> json) {
    try {
      return CharacterDetails(
        id: json['id'] as int,
        name: json['name'] as String,
        bookUrl: json['bookUrl'] as String,
        characterType: json['characterType'] as String,
        createdAt: json['createdAt'] as String,
        updatedAt: json['updatedAt'] as String,
        age: json['age'] as int?,
        gender: json['gender'] as String?,
        sex: json['sex'] as String?,
        race: json['race'] as String?,
        occupation: json['occupation'] as String?,
        personality: json['personality'] as String?,
        appearance: json['appearance'] as String?,
        backstory: json['backstory'] as String?,
        relationships: json['relationships'] as List<String>?,
        goals: json['goals'] as List<String>?,
        motivations: json['motivations'] as List<String>?,
      );
    } catch (e) {
      // Re-throw the exception to let the caller handle it
      throw FormatException('Failed to parse CharacterDetails: $e');
    }
  }
}
