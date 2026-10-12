-keepattributes Signature,*Annotation*
-keepclassmembers class ** {
    @kotlinx.serialization.Serializable <fields>;
}
