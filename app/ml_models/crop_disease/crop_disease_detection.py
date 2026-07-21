from google.colab import drive
drive.mount('/content/drive')

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau



IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20
DATASET_PATH = "/content/drive/MyDrive/Plant_leave_diseases_dataset_without_augmentation"
MODEL_OUT = "model.h5"
LABELS_OUT = "class_labels.json"


train_datagen = ImageDataGenerator(
    rescale = 1.0 / 255,
    rotation_range = 30,
    zoom_range = 0.2,
    width_shift_range = 0.2,
    height_shift_range = 0.2,
    horizontal_flip = True,
    vertical_flip = True,
    validation_split = 0.2,
)

train_gen = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size = IMAGE_SIZE,
    batch_size = BATCH_SIZE,
    class_mode = "categorical",
    subset = "training",
    shuffle = True,
)

val_gen = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size = IMAGE_SIZE,
    batch_size = BATCH_SIZE,
    class_mode = "categorical",
    subset = "validation",
    shuffle = False,
    )

NUM_CLASSES = len(train_gen.class_indices)

print(f"Number of classes: {NUM_CLASSES}")
print(f"Class Indices: {train_gen.class_indices}")

class_labels = {str(v) : k for k, v in train_gen.class_indices.items()}

with open(LABELS_OUT, "w") as f:
  json.dump(class_labels, f, indent = 2)

print(f"Class labels saved to {LABELS_OUT}")

base_model = MobileNetV2(
    input_shape = (*IMAGE_SIZE, 3),
    include_top = False,
    weights = "imagenet",
)

base_model.trainable = False

model = models.Sequential([
    base_model,

    layers.GlobalAveragePooling2D(),

    layers.Dropout(0.3),

    layers.Dense(256, activation="relu"),
    layers.BatchNormalization(),
    layers.Dropout(0.3),

    layers.Dense(NUM_CLASSES, activation = "softmax"),
])

model.compile(
    optimizer = tf.keras.optimizers.Adam(learning_rate = 1e-3),
    loss = "categorical_crossentropy",
    metrics = ["accuracy"],
)

model.summary()

callbacks = [
    EarlyStopping(
        monitor   = "val_accuracy",
        patience  = 5,
        restore_best_weights = True,
        verbose   = 1,
    ),
    ModelCheckpoint(
        filepath  = MODEL_OUT,
        monitor   = "val_accuracy",
        save_best_only = True,
        verbose   = 1,
    ),
    ReduceLROnPlateau(
        monitor   = "val_loss",
        factor    = 0.5,
        patience  = 3,
        min_lr    = 1e-6,
        verbose   = 1,
    ),
]

print("\n Phase 1: Training custom head (base model frozen)...")

history1 = model.fit(
    train_gen,
    validation_data = val_gen,
    epochs          = 10,
    callbacks       = callbacks,
)

print("\nPhase 2: Fine-tuning top layers of MobileNetV2...")

base_model.trainable = True

# Only unfreeze the last 30 layers
for layer in base_model.layers[:-30]:
    layer.trainable = False

# Recompile with a much lower learning rate for fine-tuning
model.compile(
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss      = "categorical_crossentropy",
    metrics   = ["accuracy"],
)

history2 = model.fit(
    train_gen,
    validation_data = val_gen,
    epochs          = EPOCHS,
    callbacks       = callbacks,
)

model.save(MODEL_OUT)
print(f"\n Model saved to {MODEL_OUT}")

val_loss, val_acc = model.evaluate(val_gen)
print(f"\n Final Validation Accuracy : {val_acc * 100:.2f}%")
print(f" Final Validation Loss     : {val_loss:.4f}")

def plot_history(h1, h2):
    acc  = h1.history["accuracy"]     + h2.history["accuracy"]
    val  = h1.history["val_accuracy"] + h2.history["val_accuracy"]

    plt.figure(figsize=(10, 4))
    plt.plot(acc,  label="Train Accuracy")
    plt.plot(val,  label="Val Accuracy")
    plt.title("Crop Disease Detection — Training Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.tight_layout()
    plt.savefig("training_plot.png")
    plt.show()
    print("📈 Training plot saved.")

plot_history(history1, history2)

print("\n Training complete!")
print(f"   Download  '{MODEL_OUT}'  and  '{LABELS_OUT}'")
print("   Place both in  backend/ml_models/crop_disease/")




"""for now skip this part and we train our model latter."""